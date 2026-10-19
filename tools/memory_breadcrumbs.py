"""Collection breadcrumbs, without moving pages or changing editorial content.

The city registry is the only routing authority. Secondary canonicals, pilot
pages and unregistered stories are left byte-for-byte intact. Standard library
only: the SEO and ZIP workflows do not need an additional dependency.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, unquote
import html,json,re,argparse

SITE='https://www.vivreanyons.fr'
ROOT=Path(__file__).resolve().parents[1]
NAV=re.compile(r'<nav\b[^>]*(?:ariane|breadcrumb)[^>]*>.*?</nav>',re.I|re.S)
SCRIPT=re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',re.I|re.S)
OWN='data-memory-breadcrumbs'
DROP=object()
CSS='<style data-memory-breadcrumb-style>.memory-breadcrumb{font-size:.85rem;line-height:1.8;margin-bottom:20px;overflow-wrap:anywhere}.memory-breadcrumb a{color:inherit;text-underline-offset:3px}.memory-related{font-size:.85rem;line-height:1.6}.memory-related a{color:inherit}</style>'

class Text(HTMLParser):
    def __init__(self,value):
        super().__init__(convert_charrefs=True);self.parts=[];self.feed(value)
    def handle_data(self,value):self.parts.append(value)
def clean(value):return ' '.join(''.join(Text(value).parts).split())
def escape(value):return html.escape(str(value),quote=True)
def walk(value):
    if isinstance(value,dict):
        yield value
        for v in value.values():yield from walk(v)
    elif isinstance(value,list):
        for v in value:yield from walk(v)
def is_crumb(node):
    kind=node.get('@type',[])
    return kind=='BreadcrumbList' or isinstance(kind,list) and 'BreadcrumbList' in kind
def strip_crumbs(value):
    if isinstance(value,dict):
        if is_crumb(value):return DROP
        return {k:cleaned for k,v in value.items() if (cleaned:=strip_crumbs(v)) is not DROP}
    if isinstance(value,list):return [v for n in value if (v:=strip_crumbs(n)) is not DROP]
    return value
def registry(root=ROOT):return json.loads((root/'tools/memory-cities.json').read_text(encoding='utf-8'))
def route(path,config):
    for city in config['cities']:
        if path in config.get('breadcrumb_parent_paths',[]) and path==city['path'].split('/')[0]+'/index.html':return city,False
        if path in config.get('breadcrumb_parent_paths',[]) and path==city['path'].rsplit('/',1)[0]+'/index.html':return city,False
        if path==city['path']+'/index.html':return city,False
        if path in {r['path'] for r in city['legacy']}:return city,True
        if path.startswith(city['path']+'/') and len(path.split('/'))==5 and path.endswith('/index.html'):return city,True
    return None,False
def desired(path,source,config):
    city,article=route(path,config)
    if city is None:return []
    region,department,_=city['path'].split('/')
    items=[('Accueil',SITE+'/'),('Mémoire de France',SITE+'/memoire-de-france/'),(city['region'],SITE+'/'+region+'/'),(city['department'],SITE+'/'+region+'/'+department+'/'),(city['name'],SITE+'/'+city['path']+'/')]
    if path in config.get('breadcrumb_parent_paths',[]) and path==region+'/index.html':return items[:3]
    if path in config.get('breadcrumb_parent_paths',[]) and path=='/'.join(city['path'].split('/')[:2])+'/index.html':return items[:4]
    if article:
        h=re.findall(r'<h1\b[^>]*>(.*?)</h1>',source,re.I|re.S)
        assert len(h)==1,'Exactly one H1 required: '+path
        items.append((clean(h[0]),SITE+'/'+path.removesuffix('index.html')))
    return items
def href(fragment):
    m=re.search(r'\bhref=["\']([^"\']+)["\']',fragment,re.I)
    return urljoin(SITE+'/',html.unescape(m[1])) if m else None
def schema_items(source):
    return [n for m in SCRIPT.finditer(source) for n in walk(json.loads(m[1])) if is_crumb(n)]
def item_url(item):
    value=item.get('item')
    return (value.get('@id',value.get('url')) if isinstance(value,dict) else value)
def visible_items(nav,address):
    items=[(clean(m[0]),href(m[0])) for m in re.finditer(r'<a\b[^>]*>.*?</a>',nav,re.I|re.S)]
    current=re.findall(r'<(?:span|li)\b[^>]*aria-current=["\']page["\'][^>]*>(.*?)</(?:span|li)>',nav,re.I|re.S)
    if len(current)==1:items.append((clean(current[0]),address))
    return items
def validate(source,path,config):
    expected=desired(path,source,config)
    if not expected:return []
    navs=NAV.findall(source);errors=[];address=SITE+'/'+path.removesuffix('index.html')
    if len(navs)!=1:errors.append('One visible breadcrumb required')
    visible=visible_items(navs[0],address) if len(navs)==1 else []
    if [u for _,u in visible]!=[u for _,u in expected]:errors.append('Visible route differs')
    lists=schema_items(source)
    if len(lists)!=1:errors.append('One BreadcrumbList required')
    else:
        items=lists[0].get('itemListElement',[])
        if [item_url(n) for n in items]!=[u for _,u in expected]:errors.append('Schema route differs')
        if [n.get('position') for n in items]!=list(range(1,len(expected)+1)):errors.append('Schema positions differ')
        if [(n.get('name'),item_url(n)) for n in items]!=visible:errors.append('Visible/schema labels differ')
    return errors
def apply(source,path,config=None):
    config=config or registry();expected=desired(path,source,config)
    if not expected:return source
    address=SITE+'/'+path.removesuffix('index.html')
    # Never alter aliases, differing case, pilot pages or their canonicals.
    canonical=re.findall(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)',source,re.I)
    if canonical!=[address] or re.search(r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex',source,re.I):return source
    if not validate(source,path,config):return source
    old_navs=NAV.findall(source);assert len(old_navs)<=1,'Ambiguous visible breadcrumbs: '+path
    original=old_navs[0] if old_navs else ''
    anchors={href(m[0]):m[0] for m in re.finditer(r'<a\b[^>]*>.*?</a>',original,re.I|re.S)}
    current=re.search(r'<(?:span|li)\b[^>]*aria-current=["\']page["\'][^>]*>(.*?)</(?:span|li)>',original,re.I|re.S)
    current_name=clean(current[1]) if current else expected[-1][0]
    steps=[];fragments=[];ordered=bool(re.search(r'<ol\b',original,re.I))
    for i,(name,url) in enumerate(expected):
        last=i==len(expected)-1
        fragment=anchors.get(url) if not last else None
        name=clean(fragment) if fragment else (current_name if last else name)
        steps.append((name,url))
        if last:fragment='<span aria-current="page">'+escape(name)+'</span>'
        elif fragment is None:fragment='<a href="'+url.removeprefix(SITE)+'">'+escape(name)+'</a>'
        fragments.append(('<li>'+fragment+'</li>') if ordered else fragment)
    if original:
        start=original[:original.index('>')+1]
        if re.search(r'\bclass=["\']',start):start=re.sub(r'(\bclass=["\'])',r'\1memory-breadcrumb ',start,count=1)
        else:start=start[:-1]+' class="memory-breadcrumb">'
    else:start='<nav aria-label="Fil d’Ariane" class="article-breadcrumb memory-breadcrumb">'
    nav=start+('<ol>'+''.join(fragments)+'</ol>' if ordered else ' <span aria-hidden="true">→</span> '.join(fragments))+'</nav>'
    # Preserve obsolete parent destinations as ordinary useful links, not extra
    # steps. Original editorial badges and links outside this nav remain exact.
    extras={}
    for crumb in schema_items(source):
        for item in crumb.get('itemListElement',[]):
            dest=item_url(item)
            if dest and dest not in {u for _,u in expected}:extras[dest]=item.get('name',dest)
    for dest,fragment in anchors.items():
        if dest not in {u for _,u in expected}:extras[dest]=clean(fragment)
    related=''
    if extras and 'data-memory-related' not in source:
        related='<p class="memory-related" data-memory-related>Autres rubriques : '+' · '.join('<a href="'+escape(u)+'">'+escape(name)+'</a>' for u,name in extras.items())+'</p>'
    if original:source=source.replace(original,nav+related,1)
    else:
        insertion=re.search(r'<section\b[^>]*class=["\'][^"\']*\bhero\b[^"\']*["\'][^>]*>\s*<div\b[^>]*class=["\'][^"\']*\binner\b[^"\']*["\'][^>]*>',source,re.I)
        if insertion:point=insertion.end()
        else:
            heading=re.search(r'<h1\b',source,re.I);assert heading,'Missing heading insertion point: '+path
            point=heading.start()
        source=source[:point]+nav+related+source[point:]
    def strip(m):
        value=json.loads(m[1])
        if not any(is_crumb(n) for n in walk(value)):return m[0]
        cleaned=strip_crumbs(value)
        if cleaned is DROP or isinstance(cleaned,dict) and set(cleaned)<={'@context','@graph'} and not cleaned.get('@graph'):return ''
        return m[0][:m[0].index('>')+1]+json.dumps(cleaned,ensure_ascii=False).replace('<','\\u003c')+'</script>'
    source=SCRIPT.sub(strip,source)
    schema={'@context':'https://schema.org','@type':'BreadcrumbList','@id':address+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':i,'name':name,'item':u} for i,(name,u) in enumerate(steps,1)]}
    block='<script type="application/ld+json" '+OWN+'>'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script>'
    if 'data-memory-breadcrumb-style' not in source:block=CSS+block
    source=source.replace('</head>',block+'</head>',1)
    assert not validate(source,path,config),(path,validate(source,path,config))
    return source
def scoped_paths(root,config):
    paths=set(config.get('breadcrumb_parent_paths',[]))
    for c in config['cities']:
        paths.add(c['path']+'/index.html');paths.update(r['path'] for r in c['legacy'])
        folder=root/c['path']
        if folder.is_dir():paths.update(p.relative_to(root).as_posix() for p in folder.glob('*/index.html'))
    return sorted(paths)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--apply',action='store_true');args=parser.parse_args();config=registry();pending=[]
    for path in scoped_paths(ROOT,config):
        p=ROOT/path;source=p.read_bytes().decode('utf-8');updated=apply(source,path,config)
        if updated!=source:
            pending.append(path)
            if args.apply:p.write_bytes(updated.encode('utf-8'))
    print(json.dumps({'pending':pending,'pages':len(scoped_paths(ROOT,config))},ensure_ascii=True));return bool(args.check and pending)
def apply_all(root=ROOT):
    config=registry(root);changed=[]
    for path in scoped_paths(root,config):
        target=root/path
        if not target.is_file():continue
        source=target.read_bytes().decode('utf-8');updated=apply(source,path,config)
        if updated!=source:target.write_bytes(updated.encode('utf-8'));changed.append(path)
    return changed
if __name__=='__main__':raise SystemExit(main())

"""Keep the 17 approved duplicate pages, but publish one canonical per article.

No redirects, routing, article copy, images or subdomain files are changed.
This pass runs before the existing sitemap-based SEO harmonizer.
"""
from pathlib import Path
from urllib.parse import urlsplit,urljoin,urlunsplit,unquote
from html.parser import HTMLParser
import argparse,html,json,re,subprocess,xml.etree.ElementTree as ET

SITE='https://www.vivreanyons.fr'
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'vivreanyons-test','banniere-nyons','agenda','drome'}
TAG=re.compile(r'<(?:a|link)\b[^>]*>',re.I)
HREF=re.compile(r'''(\bhref\s*=\s*)(["'])(.*?)(\2)''',re.I|re.S)
CANONICAL=re.compile(r'''<link\b(?=[^>]*\brel\s*=\s*["']canonical["'])[^>]*>''',re.I)
OG_URL=re.compile(r'''<meta\b(?=[^>]*\bproperty\s*=\s*["']og:url["'])[^>]*>''',re.I)
LD=re.compile(r'''(<script\b[^>]*\btype\s*=\s*["']application/ld\+json["'][^>]*>)(.*?)(</script>)''',re.I|re.S)
JSON_STRING=re.compile(r'"(?:[^"\\]|\\.)*"')

def mapping(root=ROOT):
    data=json.loads((root/'tools/duplicate-canonical-map.json').read_text(encoding='utf-8'))
    result={urlsplit(p['source']).path:p['target'] for p in data['pairs']}
    if len(result)!=17 or len(set(result.values()))!=17:raise ValueError('Expected the 17 approved pairs')
    for source,target in result.items():
        if not source.endswith('/') or not target.startswith(SITE+'/') or not target.endswith('/') or urlsplit(target).path in result:
            raise ValueError('Unexpected destination or chain')
    return result

def remap(raw,base,aliases):
    value=html.unescape(raw)
    if not value or value.startswith(('#','mailto:','tel:','javascript:','data:')):return raw
    try:part=urlsplit(urljoin(base,value))
    except ValueError:return raw
    if part.scheme not in ('http','https') or part.hostname not in ('www.vivreanyons.fr','vivreanyons.fr'):return raw
    path=unquote(part.path).removesuffix('index.html').rstrip('/')+'/'
    target=aliases.get(path)
    if target is None:return raw
    final=urlsplit(target)
    absolute=value.startswith(('http://','https://','//'))
    return urlunsplit((final.scheme if absolute else '',final.netloc if absolute else '',final.path,part.query,part.fragment))

def json_urls(source,base,aliases):
    def replace(match):
        raw=json.loads(match[0]);after=remap(raw,base,aliases)
        return json.dumps(after,ensure_ascii=False) if after!=raw else match[0]
    return JSON_STRING.sub(replace,source)

def hrefs(source,base,aliases):
    def attribute(a):
        after=remap(a[3],base,aliases)
        return a[0] if after==a[3] else a[1]+a[2]+html.escape(after,quote=True)+a[4]
    return TAG.sub(lambda m:HREF.sub(attribute,m[0]),source)

def update_html(source,path,aliases):
    base=SITE+'/'+path.removesuffix('index.html')
    updated=hrefs(source,base,aliases)
    updated=LD.sub(lambda m:m[1]+json_urls(m[2],base,aliases)+m[3],updated)
    route=urlsplit(base).path
    if route in aliases or base in aliases.values():
        expected=aliases.get(route,base)
        canonical='<link rel="canonical" href="'+expected+'">'
        matches=list(CANONICAL.finditer(updated))
        if matches:
            seen=False
            def canonical_tag(m):
                nonlocal seen
                if seen:return ''
                seen=True;return canonical
            updated=CANONICAL.sub(canonical_tag,updated)
        else:updated=updated.replace('</head>',canonical+'</head>',1)
        def og(m):
            return re.sub(r'''(\bcontent\s*=\s*)(["'])(.*?)(\2)''',lambda a:a[1]+a[2]+expected+a[4],m[0],count=1,flags=re.I|re.S)
        updated=OG_URL.sub(og,updated)
    return updated

def update_sitemap(source,aliases):
    def entry(m):
        loc=re.search(r'<loc>(.*?)</loc>',m[0],re.S)
        return '' if loc and urlsplit(html.unescape(loc[1])).hostname=='www.vivreanyons.fr' and urlsplit(html.unescape(loc[1])).path in aliases else m[0]
    return re.sub(r'\s*<url>.*?</url>',entry,source,flags=re.S)

def relevant(path):
    parts=Path(path).parts
    return bool(parts) and parts[0] not in EXCLUDED and not any(p.startswith('.') for p in parts)

def transform(files,aliases):
    result=dict(files)
    for path,source in files.items():
        if path.endswith('.html') and relevant(path):result[path]=update_html(source,path,aliases)
        elif path.startswith('assets/') and path.endswith('.js'):
            result[path]=hrefs(source,SITE+'/',aliases)
        elif path in ('assets/home-content.json','tools/home-editorial-updates.json','tools/immobilier-portal.json'):
            result[path]=json_urls(source,SITE+'/',aliases)
    result['sitemap.xml']=update_sitemap(files['sitemap.xml'],aliases)
    return result

class Signals(HTMLParser):
    def __init__(self,s):super().__init__();self.canonical=[];self.links=[];self.feed(s)
    def handle_starttag(self,t,attrs):
        a=dict(attrs)
        if t=='link' and 'canonical' in a.get('rel','').split():self.canonical.append(a.get('href'))
        if t=='a' and a.get('href'):self.links.append(a['href'])

def validate(files,aliases):
    urls=[n.text for n in ET.fromstring(files['sitemap.xml']).findall('{*}url/{*}loc')]
    errors=[]
    for source,target in aliases.items():
        for route in (source,urlsplit(target).path):
            path=route.lstrip('/')+'index.html'
            if path not in files:errors.append('Missing page '+path)
            elif Signals(files[path]).canonical!=[target]:errors.append('Canonical mismatch '+path)
        if SITE+source in urls:errors.append('Secondary URL in sitemap '+source)
        if urls.count(target)!=1:errors.append('Official URL missing/duplicated '+target)
    for path,source in files.items():
        if path.endswith('.html') and relevant(path):
            base=SITE+'/'+path.removesuffix('index.html')
            for raw in Signals(source).links:
                if remap(raw,base,aliases)!=raw:errors.append('Secondary internal link '+path+': '+raw)
    if errors:raise ValueError('\n'.join(errors))
    return {'pairs':len(aliases),'checked_pages':34,'sitemap_urls':len(urls)}

def install(root=ROOT,check=False,stage=False):
    root=Path(root);aliases=mapping(root)
    paths=[p for p in root.rglob('*.html') if relevant(p.relative_to(root).as_posix())]
    paths += list((root/'assets').glob('*.js'))
    paths += [root/p for p in ('sitemap.xml','assets/home-content.json','tools/home-editorial-updates.json','tools/immobilier-portal.json') if (root/p).is_file()]
    files={p.relative_to(root).as_posix():p.read_bytes().decode('utf-8') for p in paths}
    updated=transform(files,aliases);validate(updated,aliases)
    changed=[p for p in files if files[p]!=updated[p]]
    if check and changed:raise ValueError('Duplicate SEO corrections pending: '+', '.join(changed))
    if not check:
        for p in changed:
            (root/p).write_bytes(updated[p].encode('utf-8'))
            if stage:subprocess.run(['git','add','--',p],cwd=root,check=True)
    print(json.dumps({'duplicate_canonical_pages':17,'changed_files':len(changed),'sitemap_urls':len(ET.fromstring(updated['sitemap.xml']).findall('{*}url/{*}loc'))}))
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--stage',action='store_true');a=parser.parse_args();install(check=a.check,stage=a.stage)

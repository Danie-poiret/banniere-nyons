"""Index historical articles by city without relocating or editing old stories.

Only registered city indexes, their ancestor navigation and new sitemap entries
are writable. Old article HTML and old sitemap entries are read-only inputs.
"""
from pathlib import Path, PurePosixPath
import argparse, copy, html, json, re
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
from lxml import html as dom
import memory_breadcrumbs as memory_crumbs

SITE='https://www.vivreanyons.fr'
ROOT=Path(__file__).resolve().parents[1]
CONFIG='tools/memory-cities.json'
NAV_START='<!-- memory-cities-nav:start -->'
NAV_END='<!-- memory-cities-nav:end -->'

def text(node):
    return ' '.join(' '.join(node.itertext()).split())

def escape(value):
    return html.escape(str(value),quote=True)

def url(path):
    return '/'+path.removesuffix('index.html')

def read(root,path,extra):
    return extra[path] if path in extra else (root/path).read_bytes().decode('utf-8')

def schema_nodes(value):
    if isinstance(value,dict):
        yield value
        for v in value.values():yield from schema_nodes(v)
    elif isinstance(value,list):
        for v in value:yield from schema_nodes(v)

def article(root,path,summary,extra):
    source=read(root,path,extra);page=dom.fromstring(source)
    assert page.xpath('//link[@rel="canonical"]/@href')==[SITE+url(path)], 'Canonical mismatch: '+path
    headings=page.xpath('//h1');assert len(headings)==1,'Exactly one H1 required: '+path
    images=page.xpath('//main//img[@src]');assert images,'Missing article photograph: '+path
    image=images[0]
    u=urlsplit(image.get('src'));assert not u.netloc,'Local article photograph required: '+path
    image_path=unquote(u.path).lstrip('/')
    assert (root/image_path).is_file(),'Missing image: '+image_path
    assert image.get('alt') and image.get('width') and image.get('height'),'Incomplete image attributes: '+path
    descriptions=page.xpath('//meta[@name="description"]/@content')
    return {'path':path,'title':text(headings[0]),'summary':summary or (descriptions[0] if descriptions else text(headings[0])),
            'image':{k:image.get(k) for k in ('src','alt','width','height')}}

def card(a,city):
    img=a['image'];image=' '.join(k+'="'+escape(v)+'"' for k,v in img.items())
    return ('<article class="card memory-card"><a href="'+escape(url(a['path']))+'"><img '+image+' loading="lazy" decoding="async">'
            '<div class="memory-card-body"><div class="kicker">'+escape(city['name'])+'</div><h3>'+escape(a['title'])+'</h3>'
            '<p>'+escape(a['summary'])+'</p><span class="memory-read">Lire l’histoire →</span></div></a></article>')

def json_script(data):
    return json.dumps(data,ensure_ascii=False).replace('<','\\u003c')

def breadcrumbs(city):
    region,department,_=city['path'].split('/')
    return [('Accueil','/'),('Mémoire de France','/memoire-de-france/'),(city['region'],'/'+region+'/'),
            (city['department'],'/'+region+'/'+department+'/'),(city['name'],'/'+city['path']+'/')]

def city_schema(city,articles):
    address=SITE+'/'+city['path']+'/'
    return {'@context':'https://schema.org','@graph':[
        {'@type':'CollectionPage','@id':address,'url':address,'name':city['title'] or city['name']+' autrefois',
         'description':city['description'],'inLanguage':'fr-FR','mainEntity':{'@id':address+'#articles'}},
        {'@type':'ItemList','@id':address+'#articles','numberOfItems':len(articles),
         'itemListElement':[{'@type':'ListItem','position':i,'url':SITE+url(a['path']),'name':a['title']} for i,a in enumerate(articles,1)]},
        {'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i,'name':name,'item':SITE+path} for i,(name,path) in enumerate(breadcrumbs(city),1)]}]}

def city_page(root,city,articles):
    assert articles,'Refusing an empty city page'
    template=(root/'tools/templates/memory-city.html.tpl').read_text(encoding='utf-8')
    crumbs=''.join('<li>'+('<span aria-current="page">'+escape(name)+'</span>' if i==len(breadcrumbs(city))-1 else '<a href="'+escape(path)+'">'+escape(name)+'</a>')+'</li>' for i,(name,path) in enumerate(breadcrumbs(city)))
    values={'TITLE':escape(city['title']),'DESCRIPTION':escape(city['description']),'CANONICAL':escape(SITE+'/'+city['path']+'/'),
            'H1':escape(city['title']),'INTRO':escape(city['intro']),'CRUMBS':crumbs,
            'CITY':escape(city['name']),'COUNT':str(len(articles)),'CARDS':''.join(card(a,city) for a in articles),
            'SCHEMA':json_script(city_schema(city,articles)), 'OGIMAGE':escape(SITE+articles[0]['image']['src']),
            'DEPARTMENT':escape('/'+'/'.join(city['path'].split('/')[:2])+'/'),'DEPARTMENTNAME':escape(city['department']),
            'REGION':escape('/'+city['path'].split('/')[0]+'/'),'REGIONNAME':escape(city['region'])}
    for key,value in values.items():template=template.replace('@@'+key+'@@',value)
    assert not re.search(r'@@[A-Z]+@@',template),'Unknown template token'
    return template

def nav_section(cities):
    css='<style data-memory-cities-nav>.memory-cities-nav{margin:28px 0;padding:24px;border:1px solid #d6ddcf;border-radius:14px;background:#f8f6ef}.memory-cities-nav h2{font-family:Georgia,serif;color:#2a5537}.memory-cities-nav ul{display:flex;flex-wrap:wrap;gap:14px 28px;padding-left:20px}.memory-cities-nav a{color:#254b32;text-underline-offset:3px}</style>'
    links=''.join('<li><a href="/'+escape(c['path'])+'/">'+escape(c['name'])+'</a> <span>('+str(c['article_count'])+')</span></li>' for c in cities)
    return NAV_START+css+'<section class="memory-cities-nav" aria-label="Histoires par ville"><h2>Retrouver les histoires par ville</h2><ul>'+links+'</ul></section>'+NAV_END

def add_navigation(source,cities):
    block=nav_section(cities)
    if NAV_START in source:
        assert source.count(NAV_START)==source.count(NAV_END)==1,'Ambiguous navigation marker'
        return re.sub(re.escape(NAV_START)+'.*?'+re.escape(NAV_END),lambda m:block,source,flags=re.S)
    # Keep the original document, cards, scripts and all article links intact.
    m=re.search(r'<main\b[^>]*>\s*<div\b[^>]*class=["\'][^"\']*\bwrap\b[^"\']*["\'][^>]*>',source)
    assert m,'Missing navigation insertion point'
    return source[:m.end()]+block+source[m.end():]

def plan(root,config=None,extra=None):
    extra=extra or {};config=copy.deepcopy(config or json.loads((root/CONFIG).read_text(encoding='utf-8')))
    assert config['version']==1
    cities=config['cities'];changes={};records=[];all_article_paths=set()
    known_paths={p.relative_to(root).as_posix().casefold():p.relative_to(root).as_posix() for p in root.rglob('index.html') if '.git' not in p.parts and 'node_modules' not in p.parts}
    city_paths=set();city_ids=set()
    for city in cities:
        path=city['path'];parts=PurePosixPath(path).parts
        assert len(parts)==3 and all(p not in ('.','..') for p in parts) and '\\' not in path
        assert city['id'] not in city_ids and path.casefold() not in city_paths,'Duplicate city'
        city_ids.add(city['id']);city_paths.add(path.casefold())
        target=path+'/index.html'
        assert known_paths.get(target.casefold(),target)==target,'Existing city has different case: '+path
        assert (root/('/'.join(parts[:2])+'/index.html')).is_file(),'Missing or differently cased department'
        if city.get('existing'):assert (root/target).is_file(),'Existing city must never be recreated'
        old={row['path']:row['summary'] for row in city['legacy']}
        folder=root/path
        candidates=set(old)
        if folder.is_dir():candidates.update(p.relative_to(root).as_posix() for p in folder.rglob('index.html') if p.relative_to(root).as_posix()!=target)
        candidates.update(p for p in extra if p.startswith(path+'/') and p!=target and p.endswith('/index.html'))
        articles=[article(root,p,old.get(p,''),extra) for p in sorted(candidates)]
        if not articles:continue
        assert not all_article_paths.intersection(candidates),'Article assigned to more than one city'
        all_article_paths.update(candidates)
        city['article_count']=len(articles);records.append(city)
        original=read(root,target,extra) if (root/target).is_file() or target in extra else None
        if city.get('existing'):
            page=dom.fromstring(original);present={a.get('href') for a in page.xpath('//main//article[contains(concat(" ",normalize-space(@class)," ")," card ")]//a[@href]')}
            missing=[a for a in articles if url(a['path']) not in present]
            if missing:
                # Append only newly discovered stories; preserve the existing cards.
                extra_cards='<section class="region-section"><h2>Autres histoires de '+escape(city['name'])+'</h2><div class="memory-grid">'+''.join(card(a,city) for a in missing)+'</div></section>'
                updated=original.replace('</main>',extra_cards+'</main>',1)
                # Refresh only an existing generated ItemList, never canonicals.
                pattern=r'(<script\b[^>]*data-nyons-seo-auto[^>]*>)(.*?)(</script>)'
                def refresh(m):
                    data=json.loads(m[2])
                    for n in schema_nodes(data):
                        if n.get('@type')=='ItemList':
                            own=city_schema(city,articles)['@graph'][1]
                            n['numberOfItems']=own['numberOfItems'];n['itemListElement']=own['itemListElement']
                    return m[1]+json_script(data)+m[3]
                updated=re.sub(pattern,refresh,updated,flags=re.S)
                changes[target]=updated
        else:
            generated=city_page(root,city,articles)
            if generated!=original:changes[target]=generated
    # Append city navigation to existing parents. Their old links stay exact.
    parents={'memoire-de-france/index.html':records}
    for c in records:
        parts=c['path'].split('/')
        for parent in (parts[0]+'/index.html','/'.join(parts[:2])+'/index.html'):
            parents.setdefault(parent,[]).append(c)
    for path,group in parents.items():
        source=read(root,path,extra);generated=add_navigation(source,sorted(group,key=lambda c:c['name'].casefold()))
        if path=='memoire-de-france/index.html':
            # Its existing city shortcuts used department URLs as placeholders.
            # Change only these index shortcuts, never an article destination.
            for c in records:
                name=re.escape(escape(c['name']))
                pattern=r'(<a\b[^>]*href=")([^"]+)("[^>]*>\s*<strong>'+name+r'</strong>)'
                generated=re.sub(pattern,lambda m:m[1]+'/'+c['path']+'/'+m[3],generated)
        if generated!=source:changes[path]=generated
    # A newly added historical Article must use a registered city directory.
    # Existing articles (including historical aliases) are frozen exceptions.
    frozen=set(config.get('legacy_allowed_paths',[]))
    for region in ('Provence-Alpes-Cote-dAzur','Auvergne-Rhone-Alpes','Hauts-de-France','Histoire-Geo'):
        folder=root/region
        candidates={p.relative_to(root).as_posix() for p in folder.rglob('index.html')} if folder.is_dir() else set()
        candidates.update(p for p in extra if p.startswith(region+'/') and p.endswith('/index.html'))
        for path in candidates-frozen:
            if path in all_article_paths or path in {c['path']+'/index.html' for c in cities}:continue
            source=read(root,path,extra);page=dom.fromstring(source)
            types=[n.get('@type') for script in page.xpath('//script[@type="application/ld+json"]/text()') for n in schema_nodes(json.loads(script))]
            assert not any(t=='Article' or isinstance(t,list) and 'Article' in t for t in types),'New historical article outside registered city: '+path
    # Preserve every existing sitemap entry byte-for-byte; append only missing URLs.
    sitemap=read(root,'sitemap.xml',extra);tree=ET.fromstring(sitemap)
    present={e.text for e in tree.findall('{*}url/{*}loc')}
    legacy_paths={row['path'] for c in cities for row in c['legacy']}
    wanted={SITE+'/'+c['path']+'/' for c in records}|{SITE+url(p) for p in all_article_paths-legacy_paths}
    additions=''.join('  <url><loc>'+escape(u)+'</loc></url>\n' for u in sorted(wanted-present))
    if additions:
        assert '</urlset>' in sitemap
        changes['sitemap.xml']=sitemap.replace('</urlset>',additions+'</urlset>',1)
    return changes,records

def prepare_article(root,config,city_id,slug,source,definition=None):
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug),'Use a lowercase article slug'
    config=copy.deepcopy(config);matches=[c for c in config['cities'] if c['id']==city_id]
    if not matches:
        assert definition and definition['id']==city_id,'Unknown city: provide --city-definition'
        assert all(definition.get(k) for k in ('id','name','path','department','region','intro','title','description')),'Complete city editorial metadata required'
        assert not definition.get('existing') and not definition.get('legacy'),'New city must not claim legacy pages'
        definition['existing']=False;definition['legacy']=[];config['cities'].append(definition);matches=[definition]
    city=matches[0];target=city['path']+'/'+slug+'/index.html'
    assert not any(p.relative_to(root).as_posix().casefold()==target.casefold() for p in root.rglob('index.html')),'Refusing to overwrite or duplicate an existing article'
    page=dom.fromstring(source)
    nodes=[n for script in page.xpath('//script[@type="application/ld+json"]/text()') for n in schema_nodes(json.loads(script))]
    assert any(n.get('@type')=='Article' and n.get('datePublished') for n in nodes),'Prepared Article schema and original publication date required'
    # article() validates exact canonical, heading and existing local photograph.
    article(root,target,'',{target:source})
    source=memory_crumbs.apply(source,target,config)
    updates,records=plan(root,config,{target:source})
    updates[target]=source
    if definition and not [c for c in json.loads((root/CONFIG).read_text(encoding='utf-8'))['cities'] if c['id']==city_id]:
        updates[CONFIG]=json.dumps(config,ensure_ascii=False,indent=2)+'\n'
    return updates,records

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--plan-only',action='store_true')
    parser.add_argument('--add-article',nargs=3,metavar=('CITY_ID','SLUG','PREPARED_HTML'))
    parser.add_argument('--city-definition',type=Path)
    args=parser.parse_args();root=args.root.resolve()
    config=json.loads((root/CONFIG).read_text(encoding='utf-8'))
    if args.add_article:
        city,slug,file=args.add_article
        definition=json.loads(args.city_definition.read_text(encoding='utf-8')) if args.city_definition else None
        updates,records=prepare_article(root,config,city,slug,Path(file).read_text(encoding='utf-8'),definition)
    else:updates,records=plan(root,config)
    print(json.dumps({'changes':sorted(updates),'cities':[{'name':c['name'],'path':c['path'],'articles':c['article_count']} for c in records]},ensure_ascii=False,indent=2))
    if args.check:return bool(updates)
    if not args.plan_only:
        for path,source in updates.items():
            target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.encode('utf-8'))
    return 0

if __name__=='__main__':raise SystemExit(main())

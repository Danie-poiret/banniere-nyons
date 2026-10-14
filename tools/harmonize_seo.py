"""Add missing SEO in the HTML head only. Pilot scope is locked by configuration.

No dates, businesses, events, ratings or prices are inferred from page names.
Existing JSON-LD, article bodies, canonical URLs, menus and photographs are kept.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,urljoin,unquote
import json,re,html,argparse,xml.etree.ElementTree as ET,hashlib
SITE='https://www.vivreanyons.fr'
ROOT=Path(__file__).resolve().parents[1]
MARKER='data-nyons-seo-auto="v1"'
def read_source(file):
    with file.open(encoding='utf8',newline='') as stream:return stream.read()
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s))).strip()
def nodes(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():yield from nodes(child)
    elif isinstance(value,list):
        for child in value:yield from nodes(child)
class Head(HTMLParser):
    def __init__(self,source):
        super().__init__();self.meta={};self.canonical=[];self.icons=[];self.title='';self.heading='';self.images=[];self.title_on=False;self.h1_on=False;self.feed(source)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta':self.meta.setdefault(a.get('name',a.get('property','')).lower(),[]).append(a.get('content',''))
        if tag=='link':
            rel=a.get('rel','').split()
            if 'canonical' in rel:self.canonical.append(a.get('href',''))
            if 'icon' in rel:self.icons.append(a)
        if tag=='title':self.title_on=True
        if tag=='h1':self.h1_on=True
        if tag=='img' and a.get('src'):self.images.append(a)
    def handle_endtag(self,tag):
        if tag=='title':self.title_on=False
        if tag=='h1':self.h1_on=False
    def handle_data(self,s):
        if self.title_on:self.title+=s
        if self.h1_on:self.heading+=s
def schema_blocks(source):
    return [json.loads(m[1]) for m in re.finditer(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',source,re.S)]
def page_path(url):
    u=urlsplit(url)
    if u.netloc!='www.vivreanyons.fr' or u.query or u.fragment or not u.path.endswith('/'):raise ValueError('Out of scope URL: '+url)
    path=unquote(u.path).strip('/')
    file=(ROOT/(path+'/index.html' if path else 'index.html')).resolve()
    if not file.is_relative_to(ROOT.resolve()):raise ValueError('Path leaves repository')
    return file
def excerpt(source,title):
    m=re.search(r'<article\b[^>]*class=["\'][^"\']*feature-story[^"\']*["\'][^>]*>(.*?)</article>',source,re.S)
    text=m[1] if m else source.split('<main',1)[-1]
    for p in re.findall(r'<p\b[^>]*>(.*?)</p>',text,re.S):
        p=clean(p)
        if len(p)>55 and p.casefold()!=title.casefold() and not p.startswith(('Chargement','Ce contenu externe','Activez JavaScript')):
            return p if len(p)<=160 else p[:157].rsplit(' ',1)[0].rstrip(' ,;:')+'…'
    return title
def card_items(source,url,catalog):
    result=[];seen=set()
    for block in re.findall(r'<article\b[^>]*class=["\'][^"\']*\bcard\b[^"\']*["\'][^>]*>(.*?)</article>',source,re.S):
        links=re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\']',block)
        for link in links:
            dest=urljoin(url,html.unescape(link))
            if dest in catalog and dest!=url and dest not in seen:
                name=Head(catalog[dest]).title.strip()
                result.append({'@type':'ListItem','position':len(result)+1,'item':{'@type':'WebPage','@id':dest,'url':dest,'name':name}});seen.add(dest);break
    return result
def optimize(source,url,config,catalog):
    original=source
    # Rebuild only this tool's own JSON-LD; all pre-existing blocks remain exact.
    source=re.sub(r'<script\b[^>]*'+re.escape(MARKER)+r'[^>]*>.*?</script>\s*','',source,flags=re.S)
    p=Head(source);title=clean(p.title);headline=clean(p.heading) or title
    if p.canonical!=[url]:raise ValueError('Canonical requires a separate decision: '+url)
    if any('noindex' in r.lower() for r in p.meta.get('robots',[])):return original,[]
    description=p.meta.get('description',[''])[0];changes=[]
    if not description.strip() or clean(description).casefold()==title.casefold():
        replacement=excerpt(source,title)
        if replacement!=description:
            tag='<meta name="description" content="'+html.escape(replacement,quote=True)+'">'
            if 'description' in p.meta:source=re.sub(r'<meta\b[^>]*name=["\']description["\'][^>]*>',lambda _:tag,source,count=1)
            else:source=source.replace('</head>',tag+'</head>',1)
            description=replacement;changes.append('description_from_existing_text')
    existing=[n for block in schema_blocks(source) for n in nodes(block)]
    types={t for n in existing for t in (n.get('@type',[]) if isinstance(n.get('@type',[]),list) else [n['@type']])}
    kind=config.get('kinds',{}).get(url)
    if kind is None:kind='article' if re.search(r'<article\b[^>]*class=["\'][^"\']*feature-story',source) else ('collection' if len(card_items(source,url,catalog))>=2 else 'page')
    photo=p.images[0] if p.images else None
    additions=[]
    def meta(key,value):
        if value and key not in p.meta:
            additions.append('<meta '+('property' if key.startswith('og:') else 'name')+'="'+key+'" content="'+html.escape(str(value),quote=True)+'">');changes.append(key)
    meta('og:title',title);meta('og:description',description);meta('og:url',url);meta('og:type','article' if kind=='article' else 'website')
    meta('og:site_name','Vivre à Nyons');meta('og:locale','fr_FR')
    if photo:
        meta('og:image',urljoin(url,photo['src']));meta('og:image:alt',photo.get('alt',''))
        if 'og:image' not in p.meta or p.meta['og:image'][0]==urljoin(url,photo['src']):
            for key in ('width','height'):
                if str(photo.get(key,'')).isdigit():meta('og:image:'+key,photo[key])
    meta('twitter:card','summary_large_image' if photo or p.meta.get('og:image') else 'summary')
    if not p.icons:
        additions.append('<link rel="icon" type="image/png" sizes="96x96" href="/favicon-96.png"><link rel="icon" type="image/svg+xml" sizes="any" href="/favicon.svg"><link rel="shortcut icon" href="/favicon.ico">');changes.append('favicon_declarations')
    graph=[]
    if kind=='article' and not types.intersection({'Article','BlogPosting','NewsArticle'}):
        article={'@type':'Article','@id':url+'#article','headline':headline,'description':description,'mainEntityOfPage':{'@id':url},'publisher':{'@id':SITE+'/#organization'},'isPartOf':{'@id':SITE+'/#website'},'inLanguage':'fr-FR'}
        if photo:article['image']=urljoin(url,photo['src'])
        graph.append(article);changes.append('Article')
    if kind=='collection' and 'CollectionPage' not in types:
        page={'@type':'CollectionPage','@id':url,'url':url,'name':title,'description':description,'inLanguage':'fr-FR','isPartOf':{'@id':SITE+'/#website'},'publisher':{'@id':SITE+'/#organization'}}
        items=card_items(source,url,catalog)
        if items and 'ItemList' not in types:
            page['mainEntity']={'@id':url+'#items'};graph.append({'@type':'ItemList','@id':url+'#items','numberOfItems':len(items),'itemListElement':items});changes.append('ItemList')
        elif 'ItemList' in types:
            existing_list=next(n for n in existing if n.get('@type')=='ItemList')
            if existing_list.get('@id'):page['mainEntity']={'@id':existing_list['@id']}
        graph.append(page);changes.append('CollectionPage')
    if 'BreadcrumbList' not in types and url!=SITE+'/':
        crumbs=[{'@type':'ListItem','position':1,'name':'Accueil','item':SITE+'/'}]
        parts=urlsplit(url).path.strip('/').split('/')
        for n in range(1,len(parts)):
            parent=SITE+'/'+'/'.join(parts[:n])+'/'
            if parent in catalog:crumbs.append({'@type':'ListItem','position':len(crumbs)+1,'name':clean(Head(catalog[parent]).title),'item':parent})
        if url!=SITE+'/':crumbs.append({'@type':'ListItem','position':len(crumbs)+1,'name':headline,'item':url})
        graph.append({'@type':'BreadcrumbList','@id':url+'#breadcrumb','itemListElement':crumbs});changes.append('BreadcrumbList')
    business=config.get('verified_businesses',{}).get(url)
    if business and not types.intersection({'LocalBusiness','Restaurant','Hotel','LodgingBusiness','Store'}):
        item={k:v for k,v in business.items() if k not in ('source','checked')}
        item.update({'@id':url+'#establishment','mainEntityOfPage':{'@id':url}})
        if photo:item['image']=urljoin(url,photo['src'])
        graph.append(item);changes.append(item['@type'])
    event=config.get('verified_events',{}).get(url)
    if event and not types.intersection({'Event','SportsEvent'}):
        item={k:v for k,v in event.items() if k not in ('source','checked')}
        item.update({'@id':url+'#event','mainEntityOfPage':{'@id':url}})
        if photo:item['image']=urljoin(url,photo['src'])
        graph.append(item);changes.append(item['@type'])
    if graph:additions.append('<script '+MARKER+' type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False).replace('</',r'<\/')+'</script>')
    if additions:source=source.replace('</head>',''.join(additions)+'</head>',1)
    assert source.split('</head>',1)[1]==original.split('</head>',1)[1], 'Body changed'
    assert Head(source).canonical==p.canonical, 'URL changed'
    return source,changes
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--check',action='store_true');parser.add_argument('--all',action='store_true');args=parser.parse_args()
    config=json.loads((ROOT/'tools/seo-policy.json').read_text(encoding='utf8'))
    urls=[n.text for n in ET.parse(ROOT/'sitemap.xml').findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    if args.all and config.get('scope')!='global-approved':raise SystemExit('Global deployment is locked pending explicit approval.')
    selected=urls if args.all else config['pilot_urls']
    if any(u not in urls for u in selected):raise ValueError('A pilot URL is not published')
    catalog={u:read_source(page_path(u)) for u in urls}
    report=[]
    for url in selected:
        source=catalog[url];after,changes=optimize(source,url,config,catalog)
        if args.check and after!=source:raise SystemExit('Missing pilot SEO: '+url)
        if args.apply and after!=source:page_path(url).write_text(after,encoding='utf8',newline='')
        report.append({'url':url,'changed':after!=source,'changes':changes})
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

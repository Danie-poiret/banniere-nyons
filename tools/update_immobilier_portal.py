"""Update only the static article cards of the existing immobilier portal.

Curated entries keep their exact URLs. New matching pages are taken from the root
sitemap only when a real, indexable HTML file with the same canonical URL exists.
This command uses local files, the standard library, and no external API.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import html,json,re,unicodedata,xml.etree.ElementTree as ET

SITE='https://www.vivreanyons.fr'
ROOT=Path(__file__).resolve().parents[1]

def normalized(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if not unicodedata.combining(c))

def metadata(source):
    from html.parser import HTMLParser
    class Head(HTMLParser):
        def __init__(self):super().__init__();self.data={};self.in_title=False;self.title=[]
        def handle_starttag(self,t,a):
            a=dict(a)
            if t=='title':self.in_title=True
            if t=='meta' and a.get('name') in ('description','robots'):self.data[a['name']]=a.get('content','')
            if t=='link' and a.get('rel')=='canonical':self.data['canonical']=a.get('href','')
        def handle_endtag(self,t):
            if t=='title':self.in_title=False
        def handle_data(self,t):
            if self.in_title:self.title.append(t)
    p=Head();p.feed(source);p.data['title']=''.join(p.title).strip();return p.data

def classify(title):
    t=normalized(title)
    if re.search(r'hotel|camping|vacances|gite|roulotte|restaurant|location de velo',t):return None
    if 'agenc' in t and 'immobil' in t:return 'agences'
    if re.search(r'prix.*immobil|prix.*metre carre',t):return 'prix'
    if re.search(r'estim.*(?:maison|appartement|logement|immobil)|vendre.*(?:maison|appartement|logement)',t):return 'vendre'
    if re.search(r'renov|diagnostic.*immobil|isolation|dpe|travaux.*logement|urbanisme|permis de construire|demenag|plombier|climatisation|installer a nyons',t):return 'installer-renover'
    if re.search(r'ou habiter|quartier.*nyons|habiter a nyons',t):return 'habiter'
    if re.search(r'logement|location.*annee|location.*cdi|louer.*nyons',t):return 'louer'
    if re.search(r'immobilier|maisons? a vendre|appartements? a vendre|acheter.*(?:maison|appartement)',t):return 'acheter'
    return None

def page_for(url,root):
    if not url.startswith('/') or not url.endswith('/') or '?' in url or '#' in url:return None
    file=(root/unquote(url).strip('/')/'index.html').resolve()
    if not file.is_relative_to(root.resolve()) or not file.is_file():return None
    return file

def collect(root,config):
    result=[];seen=set()
    sitemap=ET.parse(root/'sitemap.xml')
    urls=[n.text for n in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc') if n.text]
    published={urlsplit(u).path for u in urls if urlsplit(u).netloc=='www.vivreanyons.fr'}
    for e in config['entries']:
        f=page_for(e['url'],root)
        if e['url'] not in published or not f:raise ValueError('Missing curated article: '+e['url'])
        data=metadata(f.read_text(encoding='utf8'))
        if data.get('canonical')!=SITE+e['url'] or 'noindex' in data.get('robots','').lower():raise ValueError('Invalid curated article: '+e['url'])
        result.append(dict(e));seen.add(e['url'])
    for u in urls:
        parsed=urlsplit(u);url=parsed.path
        if parsed.netloc!='www.vivreanyons.fr' or url in seen or url==config['portal']:continue
        if not url.startswith(('/infos-pratiques-nyons/','/questions-utiles-nyons/','/ou-dormir-a-nyons/')):continue
        f=page_for(url,root)
        if not f:continue
        data=metadata(f.read_text(encoding='utf8'));group=classify(data.get('title',''))
        if not group or data.get('canonical')!=SITE+url or 'noindex' in data.get('robots','').lower():continue
        result.append({'url':url,'group':group,'title':data['title'],'description':data.get('description','Consulte les informations et conseils de ce guide de Vivre à Nyons.'),'image':'town'});seen.add(url)
    return result

def card(e,config):
    i=config['images'][e['image']];search=e['title']+' '+e['description']+' '+e['group'].replace('-',' ')
    return '<article class="ip-card" data-portal-card data-portal-search="'+html.escape(search,quote=True)+'"><a href="'+html.escape(e['url'],quote=True)+'" aria-label="'+html.escape('Lire le guide : '+e['title'],quote=True)+'"><img src="'+i['src']+'" width="'+str(i['width'])+'" height="'+str(i['height'])+'" alt="'+html.escape(i['alt'],quote=True)+'" loading="lazy" decoding="async"><div class="ip-card-body"><h3>'+html.escape(e['title'])+'</h3><p>'+html.escape(e['description'])+'</p><span class="ip-card-link">Lire le guide →</span></div></a></article>'

def render(source,entries,config):
    for group in config['groups']:
        block='<!-- IMMOBILIER_CARDS_'+group+'_START -->';end='<!-- IMMOBILIER_CARDS_'+group+'_END -->'
        if source.count(block)!=1 or source.count(end)!=1:raise ValueError('Missing portal marker: '+group)
        cards=[card(e,config) for e in entries if e['group']==group]
        content='<div class="ip-grid">'+''.join(cards)+'</div>' if cards else ''
        source=re.sub(re.escape(block)+r'.*?'+re.escape(end),lambda m:block+content+end,source,flags=re.S)
    source=re.sub(r'(<span class="ip-count" data-portal-count>).*?(</span>)',lambda m:m[1]+str(len(entries))+m[2],source,flags=re.S)
    itemlist={'@context':'https://schema.org','@type':'ItemList','@id':SITE+config['portal']+'#guides','name':'Guides immobiliers et pratiques de Vivre à Nyons','numberOfItems':len(entries),'itemListElement':[{'@type':'ListItem','position':n,'item':{'@type':'WebPage','@id':SITE+e['url'],'name':e['title'],'url':SITE+e['url']}} for n,e in enumerate(entries,1)]}
    source=re.sub(r'(<script id="immobilier-item-list" type="application/ld\+json">).*?(</script>)',lambda m:m[1]+json.dumps(itemlist,ensure_ascii=False)+m[2],source,flags=re.S)
    return source

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    config=json.loads((ROOT/'tools/immobilier-portal.json').read_text(encoding='utf8'));file=page_for(config['portal'],ROOT)
    if not file:raise ValueError('Existing portal file is missing')
    entries=collect(ROOT,config);source=file.read_text(encoding='utf8');updated=render(source,entries,config)
    if args.check and updated!=source:raise SystemExit('The portal cards need an update')
    if not args.check and updated!=source:file.write_text(updated,encoding='utf8')
    print(f'Immobilier portal: {len(entries)} real guides, original URLs preserved.')

if __name__=='__main__':main()

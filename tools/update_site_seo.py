"""Preserve approved homepage metadata and progressively enhance the mobile menu."""
import json,re
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREFIXES=('', 'vivreanyons-test/', 'banniere-nyons/vivreanyons-test/')
TITLE='Vivre à Nyons : guide local, sorties et bonnes adresses'
DESCRIPTION='Découvrez Nyons avec un guide local : activités, restaurants, randonnées, agenda, météo, santé, services pratiques et idées en Drôme provençale.'
SCHEMA={'@context':'https://schema.org','@graph':[{'@type':'Organization','@id':'https://www.vivreanyons.fr/#organization','name':'Vivre à Nyons','url':'https://www.vivreanyons.fr/'},{'@type':'WebSite','@id':'https://www.vivreanyons.fr/#website','url':'https://www.vivreanyons.fr/','name':'Vivre à Nyons','alternateName':'VivreAnyons','inLanguage':'fr','publisher':{'@id':'https://www.vivreanyons.fr/#organization'}}]}
LABELS={'restaurants-de-nyons/':'Voir les restaurants','evenements-nyons/':'Voir les événements','randonnee-nyons/':'Choisir une randonnée','ou-dormir-a-nyons/':'Trouver un hébergement'}

def update_home(source,prefix):
    source=re.sub(r'<title>.*?</title>','<title>'+TITLE+(' — pilote' if prefix else '')+'</title>',source,count=1,flags=re.S)
    description='<meta name="description" content="'+DESCRIPTION+'">'
    source,n=re.subn(r'<meta\b[^>]*name=["\']description["\'][^>]*>',description,source,count=1)
    if n!=1: raise ValueError('Homepage description missing')
    schema=SCHEMA
    if not prefix:
        schema={**SCHEMA,'@graph':[
            {**node,
             'description':'Vivre à Nyons, guide indépendant consacré à Nyons et à la Drôme provençale : tourisme, vie locale, informations pratiques, patrimoine et mémoire du Sud.',
             'about':{'@type':'City','name':'Nyons','address':{'@type':'PostalAddress','addressLocality':'Nyons','postalCode':'26110','addressRegion':'Auvergne-Rhône-Alpes','addressCountry':'FR'}}}
            if node.get('@type')=='WebSite' else node
            for node in SCHEMA['@graph']
        ]}
    block='<script type="application/ld+json" data-home-schema>\n'+json.dumps(schema,ensure_ascii=False,indent=2)+'\n</script>'
    if 'data-home-schema' in source:
        source=re.sub(r'<script\b[^>]*data-home-schema[^>]*>.*?</script>',lambda _:block,source,count=1,flags=re.S)
    else: source=source.replace('</head>',block+'\n</head>',1)
    def card(m):
        s=m.group()
        for slug,label in LABELS.items():
            if any(h.endswith('/'+slug) for h in re.findall(r'href="([^"]+)"',s)):
                s=s.replace('<div class="kicker">Découvrir</div>','<div class="kicker">'+label+'</div>',1)
        return s
    return re.sub(r'<article\b[^>]*class=["\']card["\'][^>]*>.*?</article>',card,source,flags=re.S)

def main():
    changed=0;home_changed=False
    for prefix in PREFIXES:
        file=ROOT/(prefix+'index.html');before=file.read_text(encoding='utf-8');after=update_home(before,prefix)
        if after!=before: file.write_text(after,encoding='utf-8');changed+=1;home_changed=True
        for suffix,marker,asset in [('assets/agenda.js','installNyonsMobileNavigation','mobile-navigation.js'),('assets/style.css','Compact mobile navigation','mobile-navigation.css'),('assets/style.css','Narrow article grids','narrow-article-grids.css'),('assets/style.css','Reserve the banner','layout-stability.css')]:
            file=ROOT/(prefix+suffix);before=file.read_text(encoding='utf-8')
            addition=(ROOT/'tools/seo-assets'/asset).read_text(encoding='utf-8')
            if marker not in before: file.write_text(before.rstrip()+'\n\n'+addition,encoding='utf-8');changed+=1
    if home_changed:
        file=ROOT/'sitemap.xml';source=file.read_text(encoding='utf-8');today=datetime.now(ZoneInfo('Europe/Paris')).date().isoformat()
        def home_entry(m):
            node=m.group()
            if '<loc>https://www.vivreanyons.fr/</loc>' not in node:return node
            if '<lastmod>' in node:return re.sub(r'<lastmod>.*?</lastmod>','<lastmod>'+today+'</lastmod>',node)
            return node.replace('</url>','<lastmod>'+today+'</lastmod></url>')
        after=re.sub(r'<url>.*?</url>',home_entry,source,flags=re.S)
        if after!=source:file.write_text(after,encoding='utf-8');changed+=1
    # ZIP updates run this pass before integrity checks. Repair only registered
    # primary collection routes, never pilot pages, aliases or other content.
    from memory_breadcrumbs import apply_all
    changed += len(apply_all(ROOT))
    print(f'Site SEO and mobile navigation: {changed} files updated.')
if __name__=='__main__': main()

"""Add one reviewed story to an existing city without scanning other cities."""
import argparse,json,re
from pathlib import Path
from lxml import html
import update_memory_cities as memory
import memory_breadcrumbs
import memory_recent

def prepare(root,city_id,slug,source,refresh=False):
    config=json.loads((root/memory.CONFIG).read_text(encoding='utf-8'))
    city=next((c for c in config['cities'] if c['id']==city_id),None)
    assert city,'Unknown city: use update_memory_cities.py for a new city'
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug),'Invalid slug'
    target=city['path']+'/'+slug+'/index.html';folder=root/city['path']
    assert folder.is_dir() and (folder/'index.html').is_file(),'Existing city required'
    existing=[p for p in folder.iterdir() if p.name.casefold()==slug.casefold()]
    if refresh:
        assert len(existing)==1 and existing[0].name==slug and (root/target).is_file(),'Exact existing article required for refresh'
        old=html.fromstring((root/target).read_text(encoding='utf-8'))
        before=[n.get('datePublished') for s in old.xpath('//script[@type="application/ld+json"]/text()') for n in memory.schema_nodes(json.loads(s)) if n.get('@type')=='Article' or isinstance(n.get('@type'),list) and 'Article' in n['@type']]
    else:
        assert not existing,'Article already exists or differs only by case'
    article=memory.article(root,target,'',{target:source})
    dom=html.fromstring(source)
    schemas=[n for s in dom.xpath('//script[@type="application/ld+json"]/text()') for n in memory.schema_nodes(json.loads(s))]
    dates=[n.get('datePublished') for n in schemas if n.get('@type')=='Article' or isinstance(n.get('@type'),list) and 'Article' in n['@type']]
    assert dates and all(memory_recent.timestamp(d) for d in dates),'Article and valid original publication date required'
    if refresh:assert dates==before,'Refresh must preserve original datePublished'
    updates={target:memory_breadcrumbs.apply(source,target,config)}
    citypath=city['path']+'/index.html';original=(root/citypath).read_text(encoding='utf-8')
    assert html.fromstring(original).xpath('//link[@rel="canonical"]/@href')==[memory.SITE+'/'+city['path']+'/'],'Wrong city canonical; refresh this exact file from GitHub'
    if not refresh:assert memory.url(target) not in html.fromstring(original).xpath('//main//article//a/@href'),'Duplicate story link'
    grids=list(re.finditer(r'<div\b[^>]*class=["\'][^"\']*\bmemory-grid\b[^"\']*["\'][^>]*>',original))
    assert len(grids)==1,'Existing city must have one article grid'
    if refresh:
        matches=[m for m in re.finditer(r'<article\b[^>]*>[\s\S]*?</article>',original) if memory.url(target) in html.fromstring(m[0]).xpath('.//a/@href')]
        assert len(matches)==1,'Exactly one existing city card required for refresh'
        match=matches[0];updated=original[:match.start()]+memory.card(article,city)+original[match.end():]
    else:
        at=grids[0].end();updated=original[:at]+memory.card(article,city)+original[at:]
    cards=html.fromstring(updated).xpath('//main//article[contains(concat(" ",normalize-space(@class)," ")," card ")]')
    count=len(cards)
    updated=re.sub(r'(<p\b[^>]*class=["\']city-count["\'][^>]*>)\d+',lambda m:m[1]+str(count),updated)
    def schema(match):
        data=json.loads(match[2])
        for node in memory.schema_nodes(data):
            if node.get('@type')=='ItemList' and isinstance(node.get('itemListElement'),list):
                items=node['itemListElement']
                if refresh:
                    own=[item for item in items if item.get('url')==memory.SITE+memory.url(target)]
                    assert len(own)==1,'Exactly one existing schema entry required for refresh'
                    own[0]['name']=article['title']
                else:
                    assert not any(item.get('url')==memory.SITE+memory.url(target) for item in items),'Duplicate schema entry'
                    items.insert(0,{'@type':'ListItem','position':1,'url':memory.SITE+memory.url(target),'name':article['title']})
                for i,item in enumerate(items,1):item['position']=i
                node['numberOfItems']=len(items)
        return match[1]+memory.json_script(data)+match[3]
    updated=re.sub(r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)([\s\S]*?)(</script>)',schema,updated)
    updates[citypath]=updated
    region,department,_=city['path'].split('/')
    for parent in ['memoire-de-france/index.html',region+'/index.html',region+'/'+department+'/index.html']:
        page=(root/parent).read_text(encoding='utf-8')
        canonical=html.fromstring(page).xpath('//link[@rel="canonical"]/@href')
        assert canonical==[memory.SITE+memory.url(parent)],'Wrong parent canonical; refresh this exact file from GitHub: '+parent
        pattern=r'(<a\b[^>]*href=["\']'+re.escape('/'+city['path']+'/')+r'["\'][^>]*>[\s\S]*?</a>\s*<span>\()\d+(\)</span>)'
        new=re.sub(pattern,lambda m:m[1]+str(count)+m[2],page)
        if new!=page:updates[parent]=new
    sitemap=(root/'sitemap.xml').read_text(encoding='utf-8');url=memory.SITE+memory.url(target)
    if refresh:
        assert '<loc>'+url+'</loc>' in sitemap,'Existing story missing from sitemap'
    else:
        assert '<loc>'+url+'</loc>' not in sitemap,'Duplicate sitemap URL'
        updates['sitemap.xml']=sitemap.replace('</urlset>','  <url><loc>'+url+'</loc></url>\n</urlset>',1)
    # Commit the hub's recent cards with the story, not in a later workflow.
    updates.update(memory_recent.plan(root,config,updates))
    assert len(updates)<=7
    return updates

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('city');p.add_argument('slug');p.add_argument('prepared',type=Path);p.add_argument('--root',type=Path,default=memory.ROOT);p.add_argument('--plan-only',action='store_true');p.add_argument('--refresh',action='store_true',help='Refresh an existing story and its cards without changing its original publication date');args=p.parse_args()
    root=args.root.resolve();updates=prepare(root,args.city,args.slug,args.prepared.read_text(encoding='utf-8'),refresh=args.refresh)
    print(json.dumps({'changes':list(updates),'home_unchanged':True},ensure_ascii=False,indent=2))
    if not args.plan_only:
        for path,source in updates.items():
            target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source,encoding='utf-8')
if __name__=='__main__':main()

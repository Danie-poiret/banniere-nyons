"""Add one reviewed story to an existing city without scanning other cities."""
import argparse,json,re
from pathlib import Path
from lxml import html
import update_memory_cities as memory
import memory_breadcrumbs

def prepare(root,city_id,slug,source):
    config=json.loads((root/memory.CONFIG).read_text(encoding='utf-8'))
    city=next((c for c in config['cities'] if c['id']==city_id),None)
    assert city,'Unknown city: use update_memory_cities.py for a new city'
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug),'Invalid slug'
    target=city['path']+'/'+slug+'/index.html';folder=root/city['path']
    assert folder.is_dir() and (folder/'index.html').is_file(),'Existing city required'
    assert not any(p.name.casefold()==slug.casefold() for p in folder.iterdir()),'Article already exists or differs only by case'
    article=memory.article(root,target,'',{target:source})
    dom=html.fromstring(source)
    schemas=[n for s in dom.xpath('//script[@type="application/ld+json"]/text()') for n in memory.schema_nodes(json.loads(s))]
    assert any(n.get('@type')=='Article' and n.get('datePublished') for n in schemas),'Article and original publication date required'
    updates={target:memory_breadcrumbs.apply(source,target,config)}
    citypath=city['path']+'/index.html';original=(root/citypath).read_text(encoding='utf-8')
    assert html.fromstring(original).xpath('//link[@rel="canonical"]/@href')==[memory.SITE+'/'+city['path']+'/'],'Wrong city canonical; refresh this exact file from GitHub'
    assert memory.url(target) not in html.fromstring(original).xpath('//main//article//a/@href'),'Duplicate story link'
    grids=list(re.finditer(r'<div\b[^>]*class=["\'][^"\']*\bmemory-grid\b[^"\']*["\'][^>]*>',original))
    assert len(grids)==1,'Existing city must have one article grid'
    at=grids[0].end();updated=original[:at]+memory.card(article,city)+original[at:]
    cards=html.fromstring(updated).xpath('//main//article[contains(concat(" ",normalize-space(@class)," ")," card ")]')
    count=len(cards)
    updated=re.sub(r'(<p\b[^>]*class=["\']city-count["\'][^>]*>)\d+',lambda m:m[1]+str(count),updated)
    def schema(match):
        data=json.loads(match[2])
        for node in memory.schema_nodes(data):
            if node.get('@type')=='ItemList' and isinstance(node.get('itemListElement'),list):
                items=node['itemListElement']
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
    assert '<loc>'+url+'</loc>' not in sitemap,'Duplicate sitemap URL'
    updates['sitemap.xml']=sitemap.replace('</urlset>','  <url><loc>'+url+'</loc></url>\n</urlset>',1)
    assert len(updates)<=6
    return updates

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('city');p.add_argument('slug');p.add_argument('prepared',type=Path);p.add_argument('--root',type=Path,default=memory.ROOT);p.add_argument('--plan-only',action='store_true');args=p.parse_args()
    root=args.root.resolve();updates=prepare(root,args.city,args.slug,args.prepared.read_text(encoding='utf-8'))
    print(json.dumps({'changes':list(updates),'home_unchanged':True},ensure_ascii=False,indent=2))
    if not args.plan_only:
        for path,source in updates.items():
            target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source,encoding='utf-8')
if __name__=='__main__':main()

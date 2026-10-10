"""Refresh only the main homepage from the existing agenda; no AI generation."""
import argparse,html,json,re,subprocess
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
from update_latest_article import update as update_articles

ROOT=Path(__file__).resolve().parents[1]
FEED='https://raw.githubusercontent.com/Danie-poiret/agenda-nyons/main/'
def read_source(name):
    with urlopen(Request(FEED+name,headers={'User-Agent':'VivreAnyons-home/1.0','Cache-Control':'no-cache'}),timeout=35) as response:
        body=response.read(2_000_001)
        if len(body)>2_000_000:raise ValueError('Oversized source')
        return body.decode('utf-8')
def summary(value):
    value=html.unescape(re.sub(r'\s+',' ',str(value or ''))).strip()
    value=value.split('Abonnement aux informations de la ville de Nyons')[0]
    value=re.sub(r'\s+1 2 3 4 5.*$','',value).strip()
    return value if len(value)<=205 else value[:204].rsplit(' ',1)[0]+'…'
def normalize(feed,cache,details,published):
    rows=[]
    for e in feed.get('events',[]):
        saved=cache.get(e.get('url'),{});practical=details.get(e.get('url'),{}).get('practical') or saved.get('practical') or {}
        url=e.get('page_url') or (f'{"https://agenda.vivreanyons.fr/evenements/"}{saved["slug"]}/' if saved.get('slug') else e.get('url',''))
        if not re.fullmatch(r'https://agenda\.vivreanyons\.fr/evenements/[^/?#]+/',url) or url not in published:continue
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',e.get('start_date','')):continue
        dt=practical.get('date_time','');raw_times=re.findall(r'(\d{1,2})[h:](\d{2})',dt)
        times=['%02d:%02d'%(int(h),int(m)) for h,m in raw_times if int(h)<24 and int(m)<60]
        rows.append({'title':e['title'],'url':url,'start':e['start_date'],'end':e.get('end_date') or e['start_date'],'startTime':times[0] if times else '', 'endTime':times[-1] if len(times)>=2 else '', 'dateTime':dt,'place':(practical.get('location_name') or practical.get('address') or ('Cinéma L’Arlequin' if e.get('kind')=='cinema' else '')).rstrip(' ,'),'summary':summary(saved.get('editorial',{}).get('intro') or e.get('summary')),'kind':e.get('kind','event'),'sessions':[s for s in e.get('sessions',[]) if re.fullmatch(r'\d{4}-\d{2}-\d{2}',s.get('date','')) and re.fullmatch(r'\d{2}:\d{2}',s.get('time',''))]})
    return rows
def select(root,data,at=None):
    script="const fs=require('node:fs'),a=require('./assets/home.js'),d=JSON.parse(fs.readFileSync(0,'utf8')),now=d.at?new Date(d.at):new Date();console.log(JSON.stringify({events:a.select(d.events,now),day:a.stamp(now).slice(0,10),season:a.season(a.stamp(now).slice(0,10))}));"
    run=subprocess.run(['node','-e',script],input=json.dumps({'events':data['events'],'at':at}),text=True,capture_output=True,cwd=root,check=True)
    return json.loads(run.stdout)
MONTHS=['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']
def date_fr(day):
    y,m,d=day[:10].split('-');return f'{int(d)} {MONTHS[int(m)-1]} {y}'
E=lambda value:html.escape(str(value),quote=True)
def render_events(events,day):
    cards=[]
    for e in events[:5]:
        visible=max(e['start'],day)
        badge='<span class="home-badge">Aujourd’hui</span>' if e['today'] else '<span class="home-badge">Ce week-end</span>' if e['weekend'] else ''
        when=e['dateTime'] or date_fr(e['start']);place=e['place']+(' · ' if e['place'] and when else '')+when
        cards.append(f'<article class="home-event{" is-today" if e["today"] else ""}"><div class="home-event-date"><strong>{int(visible[8:10])}</strong>{MONTHS[int(visible[5:7])-1][:4]}<br>{visible[:4]}</div><div>{badge}<h3><a href="{E(e["url"])}">{E(e["title"])}</a></h3><p class="home-event-place">{E(place)}</p><p>{E(e["summary"])}</p></div></article>')
    return ''.join(cards) or '<p>Les prochaines dates sont à retrouver dans <a href="https://agenda.vivreanyons.fr/">l’agenda de Nyons</a>.</p>'
def refresh(root,fixture=None):
    target=root/'assets/home-content.json';old=json.loads(target.read_text(encoding='utf-8'))
    names=['agenda.json','_event_seo_cache.json','_event_detail_cache.json','sitemap.xml']
    try:
        if fixture:
            fixture_data=json.loads(fixture.read_text(encoding='utf-8'))
            feed=fixture_data['agenda'];cache={k:{'slug':v.get('slug'),'editorial':{'intro':v.get('intro')},'practical':v.get('practical')} for k,v in fixture_data['editorial'].items()};details={};published=set(fixture_data['published'])
        else:
            with ThreadPoolExecutor(max_workers=4) as pool:sources=dict(zip(names,pool.map(read_source,names)))
            feed=json.loads(sources['agenda.json']);cache=json.loads(sources['_event_seo_cache.json']);details=json.loads(sources['_event_detail_cache.json']);published=set(re.findall(r'<loc>([^<]+)</loc>',sources['sitemap.xml']))
        rows=normalize(feed,cache,details,published)
        if not rows:raise ValueError('No published event found')
        data={**old,'events':rows,'sourceUpdated':feed['updated_at'],'sourceStatus':'available'}
    except Exception as error:
        print('Agenda source temporarily unavailable; preserving previous data: '+str(error));data={**old,'sourceStatus':'cached'}
    selected=select(root,data);data['generatedAt']=datetime.now(timezone.utc).isoformat(timespec='seconds')
    update_articles(root)
    page=root/'index.html';source=page.read_text(encoding='utf-8')
    source,n=re.subn(r'<!-- HOME_EVENTS_START -->.*?<!-- HOME_EVENTS_END -->',lambda _: '<!-- HOME_EVENTS_START -->'+render_events(selected['events'],selected['day'])+'<!-- HOME_EVENTS_END -->',source,count=1,flags=re.S)
    if n!=1:raise ValueError('Missing homepage event markers')
    season=data['seasons'][selected['season']]
    season_html='<div class="kicker">Au fil des saisons</div><h2>'+E(season['title'])+'</h2><div class="home-season-grid" data-home-season-cards>'+''.join(f'<article class="home-season-card"><h3><a href="{E(i["url"])}">{E(i["title"])}</a></h3><p>{E(i["summary"])}</p></article>' for i in season['items'])+'</div>'
    source,n=re.subn(r'<!-- HOME_SEASON_START -->.*?<!-- HOME_SEASON_END -->',lambda _: '<!-- HOME_SEASON_START -->'+season_html+'<!-- HOME_SEASON_END -->',source,count=1,flags=re.S)
    if n!=1:raise ValueError('Missing homepage season markers')
    body=json.dumps(data,ensure_ascii=False,separators=(',',':'))
    source,n=re.subn(r'(<script type="application/json" data-home-content>).*?(</script>)',lambda m:m[1]+body.replace('</','<\\/')+m[2],source,count=1,flags=re.S)
    if n!=1:raise ValueError('Missing homepage snapshot')
    status='Agenda actualisé le '+date_fr(data['sourceUpdated'][:10])+'.'
    if data['sourceStatus']=='cached':status+=' Dernières données conservées pendant une interruption de la source.'
    source=re.sub(r'(<p class="home-data-status">).*?(</p>)',lambda m:m[1]+E(status)+m[2],source,count=1,flags=re.S)
    page.write_text(source,encoding='utf-8');target.write_text(body+'\n',encoding='utf-8')
    print(json.dumps({'homepageOnly':True,'sourceStatus':data['sourceStatus'],'events':len(selected['events'][:5]),'day':selected['day'],'season':selected['season']}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--fixture',type=Path)
    args=parser.parse_args();refresh(args.root.resolve(),args.fixture)

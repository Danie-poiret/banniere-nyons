"""Publish only regular services through Nyons, from official open GTFS feeds.

Calendar exceptions, boarding/alighting restrictions and reservation flags are
kept. These are planned times, never claimed to be real-time predictions.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import argparse, csv, io, json, re, zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'drome':('607860847e79b65f245982db','Cars Région Drôme','https://transport.data.gouv.fr/datasets/reseau-interurbain-et-scolaire-cars-region-drome-26','ODbL'),
 'express':('61b36a0610344080a78cf407','Cars Région Express','https://transport.data.gouv.fr/datasets/reseau-interurbain-cars-region-express','ODbL'),
 'zou':('668d0a18a847603d391cbeec','ZOU ! Proximité','https://transport.data.gouv.fr/datasets/lignes-des-reseaux-transport-zou-provence-alpes-cote-d-azur-proximite-3-3','Licence Ouverte 2.0'),
}
ALLOWED={'drome':{'D36','D37','D38','D39','D44','D45'},'express':{'X71'},'zou':{'924'}}
WEEK=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
def fetch(url,limit=40_000_000):
    with urlopen(Request(url,headers={'User-Agent':'VivreAnyons/1.0 (contact@vivreanyons.fr)','Accept':'application/json,application/zip','Cache-Control':'no-cache'}),timeout=45) as r:
        body=r.read(limit+1)
        if len(body)>limit:raise ValueError('Oversized response')
        return body
def seconds(value):
    if not re.fullmatch(r'\d{1,2}:\d{2}:\d{2}',value or ''):return None
    h,m,s=map(int,value.split(':'))
    return h*3600+m*60+s if h<72 and m<60 and s<60 else None
def commune(stop):
    m=re.search(r'^FR:(\d{5}):|-(\d{5})\d{2}(?:C)?$',stop['stop_id'])
    return (m[1] or m[2]) if m else ''
def parse_gtfs(body,key,cities,coverage=None):
    z=zipfile.ZipFile(io.BytesIO(body))
    def rows(name,optional=False):
        names=[n for n in z.namelist() if n.split('/')[-1]==name]
        if not names:
            if optional:return []
            raise ValueError('Missing '+name)
        if len(names)!=1 or z.getinfo(names[0]).file_size>80_000_000:raise ValueError('Invalid member '+name)
        return csv.DictReader(io.TextIOWrapper(z.open(names[0]),encoding='utf-8-sig'))
    stops={s['stop_id']:s for s in rows('stops.txt')}
    nyons={i for i,s in stops.items() if commune(s)=='26220' and s.get('location_type','0') in ('','0')}
    if not nyons:raise ValueError('No Nyons boarding stops')
    routes={r['route_id']:r for r in rows('routes.txt') if r['route_short_name'] in ALLOWED[key] and 'SCO' not in r.get('route_long_name','').upper()}
    trips={t['trip_id']:t for t in rows('trips.txt') if t['route_id'] in routes}
    timed={i:[] for i in trips}
    for s in rows('stop_times.txt'):
        if s['trip_id'] not in trips:continue
        arrival=seconds(s.get('arrival_time',''));departure=seconds(s.get('departure_time',''))
        # No interpolation or invented times for untimed/flexible stops.
        if arrival is None or departure is None:continue
        timed[s['trip_id']].append((int(s['stop_sequence']),s['stop_id'],arrival,departure,int(s.get('pickup_type') or 0),int(s.get('drop_off_type') or 0)))
    frequency_trips={r['trip_id'] for r in rows('frequencies.txt',True)}
    selected={i:sorted(sts) for i,sts in timed.items() if i not in frequency_trips and any(s[1] in nyons for s in sts)}
    if not selected:raise ValueError('No fixed regular trips through Nyons')
    used_stops={s[1] for sts in selected.values() for s in sts};used_routes={trips[i]['route_id'] for i in selected};used_services={trips[i]['service_id'] for i in selected}
    ns=lambda ident:key+':'+ident
    calendars={}
    for c in rows('calendar.txt',True):
        if c['service_id'] in used_services:
            calendars[c['service_id']]={'start':c['start_date'],'end':c['end_date'],'week':[int(c[d]) for d in WEEK],'added':[],'removed':[]}
    for c in rows('calendar_dates.txt',True):
        if c['service_id'] not in used_services:continue
        service=calendars.setdefault(c['service_id'],{'start':'','end':'','week':[0]*7,'added':[],'removed':[]})
        if c['exception_type'] not in ('1','2'):raise ValueError('Invalid calendar exception')
        service['added' if c['exception_type']=='1' else 'removed'].append(c['date'])
    if used_services-set(calendars):raise ValueError('Missing service calendars')
    dates=[d for c in calendars.values() for d in [c['start'],c['end'],*c['added']] if d]
    start=min(dates);end=max(dates)
    if coverage:
        start=max(start,coverage.get('start_date','').replace('-','') or start)
        end=min(end,coverage.get('end_date','').replace('-','') or end)
    result={'routes':{},'stops':{},'services':{ns(i):v for i,v in calendars.items()},'trips':[],'start':start,'end':end}
    for i in used_stops:
        s=stops[i];code=commune(s)
        result['stops'][ns(i)]={'name':s['stop_name'],'city':cities.get(code,code),'cityCode':code,'nyons':i in nyons}
    for i in used_routes:
        r=routes[i];result['routes'][ns(i)]={'number':r['route_short_name'],'name':r['route_long_name'],'source':key}
    for i,sts in selected.items():
        t=trips[i];result['trips'].append({'id':ns(i),'route':ns(t['route_id']),'service':ns(t['service_id']),'stops':[[ns(s[1]),*s[2:]] for s in sts]})
    return result
def refresh(root,cached=None):
    old_path=root/'assets/bus-nyons.json'
    old=json.loads(old_path.read_text(encoding='utf-8')) if old_path.exists() else {}
    try:
        cities=json.loads((cached/'communes.json').read_text(encoding='utf-8')) if cached else json.loads(fetch('https://geo.api.gouv.fr/communes?fields=nom,code',5_000_000))
        cities={c['code']:c['nom'] for c in cities}
    except Exception:
        cities={s['cityCode']:s['city'] for s in old.get('stops',{}).values() if s.get('cityCode') and s.get('city')}
        if not cities:raise ValueError('No verified commune labels')
    now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    result={'version':1,'generatedAt':now,'sources':{},'routes':{},'stops':{},'services':{},'trips':[]}
    for key,(dataset,label,page,license_name) in SOURCES.items():
        source={'label':label,'url':page,'license':license_name}
        try:
            metadata=json.loads((cached/(key+'-meta.json')).read_text(encoding='utf-8')) if cached else json.loads(fetch('https://transport.data.gouv.fr/api/datasets/'+dataset,5_000_000))
            resource=next(r for r in metadata['resources'] if r.get('format','').upper()=='GTFS' and r.get('type')=='main')
            body=(cached/(key+'.zip')).read_bytes() if cached else fetch(resource['url'])
            data=parse_gtfs(body,key,cities,resource.get('metadata'))
            source.update(status='available',checkedAt=now,sourceUpdated=resource.get('updated'),start=data.pop('start'),end=data.pop('end'))
        except Exception as error:
            print(key+': source unavailable: '+str(error))
            previous=old.get('sources',{}).get(key,{})
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(previous['checkedAt'])).total_seconds() if previous.get('checkedAt') else float('inf')
            if age<3*86400:
                source={**previous,'status':'cached','failedAt':now}
                data={field:{i:v for i,v in old.get(field,{}).items() if i.startswith(key+':')} for field in ['routes','stops','services']}
                data['trips']=[t for t in old.get('trips',[]) if t['id'].startswith(key+':')]
            else:source.update(status='unavailable',failedAt=now);data={}
        result['sources'][key]=source
        for field in ['routes','stops','services']:result[field].update(data.get(field,{}))
        result['trips'].extend(data.get('trips',[]))
    if not result['trips'] and not old:raise ValueError('No usable initial source; do not publish empty schedules')
    body=json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n'
    for prefix in ['', 'vivreanyons-test/','banniere-nyons/vivreanyons-test/']:
        target=root/(prefix+'assets/bus-nyons.json');target.parent.mkdir(parents=True,exist_ok=True)
        temp=target.with_suffix('.tmp');temp.write_text(body,encoding='utf-8');temp.replace(target)
    print(json.dumps({'sources':{k:v['status'] for k,v in result['sources'].items()},'routes':len(result['routes']),'trips':len(result['trips']),'json_bytes':len(body.encode('utf-8'))}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--cached-dir',type=Path)
    args=p.parse_args();refresh(args.root,args.cached_dir)

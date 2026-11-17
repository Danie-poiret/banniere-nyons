"""Refresh only the loto calendar and next-event answer, preserving the article."""
import argparse,json,re,subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.request import Request,urlopen
from html import escape

ROOT=Path(__file__).resolve().parents[1]
PAGE='lotos-nyons/index.html'
FEED='https://agenda.vivreanyons.fr/agenda.json'

def replace(source,pattern,value):
 result,count=re.subn(pattern,lambda _:value,source,count=1,flags=re.S)
 if count!=1:raise ValueError('Missing loto marker: '+pattern)
 return result

def refresh(root=ROOT,fixture=None,at=None):
 now=datetime.fromisoformat(at) if at else datetime.now(ZoneInfo('Europe/Paris'))
 if now.tzinfo is None:raise ValueError('Timezone required')
 target=root/PAGE;source=target.read_text(encoding='utf8')
 previous=json.loads(re.search(r'<script type="application/json" id="loto-data">(.*?)</script>',source,re.S)[1])
 payload={'at':now.isoformat()}
 try:
  if fixture:feed=json.loads(fixture.read_text(encoding='utf8'))
  else:
   with urlopen(Request(FEED,headers={'User-Agent':'VivreAnyons-loto/1.0','Cache-Control':'no-cache'}),timeout=25) as response:
    body=response.read(2_000_001)
   if len(body)>2_000_000:raise ValueError('Oversized source')
   feed=json.loads(body)
  if not isinstance(feed.get('events'),list):raise ValueError('Invalid feed')
  payload.update(feed=feed,status='available')
 except Exception as error:
  print('Agenda unavailable; retaining and pruning previous dates: '+str(error))
  payload.update(data=previous,status='cached')
 script="const a=require('./assets/loto-nyons.js'),fs=require('node:fs'),p=JSON.parse(fs.readFileSync(0,'utf8'));let d=p.feed?a.normalize(p.feed):p.data;d.status=p.status;const e=a.select(d,new Date(p.at));d.events=e;console.log(JSON.stringify({data:d,html:a.render(e),next:a.nextText(e),source:a.sourceText(d),count:e.length}));"
 run=subprocess.run(['node','-e',script],input=json.dumps(payload),cwd=root,text=True,capture_output=True,check=True,encoding='utf8')
 built=json.loads(run.stdout)
 source=replace(source,r'<!-- LOTO_RESULTS_START -->.*?<!-- LOTO_RESULTS_END -->','<!-- LOTO_RESULTS_START -->'+built['html']+'<!-- LOTO_RESULTS_END -->')
 source=replace(source,r'<script type="application/json" id="loto-data">.*?</script>','<script type="application/json" id="loto-data">'+json.dumps(built['data'],ensure_ascii=False,separators=(',',':')).replace('</',r'<\/')+'</script>')
 source=replace(source,r'<p data-loto-next>.*?</p>','<p data-loto-next>'+escape(built['next'])+'</p>')
 source=replace(source,r'<p data-loto-source[^>]*>.*?</p>','<p data-loto-source class="loto-source">'+escape(built['source'])+'</p>')
 source=replace(source,r'<p data-loto-status[^>]*>.*?</p>','<p data-loto-status role="status" aria-live="polite">'+str(built['count'])+' annonce(s) de loto à venir.</p>')
 if target.read_text(encoding='utf8')!=source:target.write_text(source,encoding='utf8',newline='')
 print(json.dumps({'page':PAGE,'upcoming':built['count'],'sourceStatus':built['data']['status']}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--fixture',type=Path);parser.add_argument('--at');args=parser.parse_args()
 refresh(fixture=args.fixture,at=args.at)

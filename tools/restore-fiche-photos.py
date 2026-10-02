#!/usr/bin/env python3
"""Restore the user's public Google Sites photographs without altering fiche content."""
import concurrent.futures,hashlib,io,json,re,time,urllib.request
from pathlib import Path
from lxml import html,etree
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/'tools/restore-fiche-photos-manifest.json').read_text('utf8'))
PREFIXES=['','vivreanyons-test/','banniere-nyons/vivreanyons-test/']
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def safe(path):
 p=(ROOT/path).resolve()
 if not p.is_relative_to(ROOT) or '.git' in p.parts:raise ValueError('Invalid output path')
 return p
for path,sha in MANIFEST['expected_sha'].items():
 assert blob(safe(path).read_bytes())==sha, 'Page changed since review: '+path
def get(url):
 assert url.startswith(('https://sites.google.com/','https://lh7-us.googleusercontent.com/','https://lh3.googleusercontent.com/'))
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://sites.google.com/'}),timeout=45) as f:
  assert f.status==200
  return f.read()
def sources(row):
 d=html.fromstring(get(row['source']+'?photos='+str(time.time_ns())));seen=set();urls=[]
 for n in d.xpath('//img[contains(concat(" ",normalize-space(@class)," ")," CENy8b ")]'):
  if n.xpath('ancestor::header|ancestor::nav|ancestor::footer'):continue
  u=n.get('src','');k=re.sub(r'=w\d+.*$','',u)
  if u and k not in seen:seen.add(k);urls.append(u)
 assert len(urls)==row['count'],(row['path'],len(urls),row['count'])
 return urls
def optimize(raw):
 im=ImageOps.exif_transpose(Image.open(io.BytesIO(raw)));im.load();assert min(im.size)>=30
 im.thumbnail((1280,1280),Image.Resampling.LANCZOS);im=im.convert('RGB')
 for q in (78,70,62):
  out=io.BytesIO();im.save(out,'WEBP',quality=q,method=4)
  if out.tell()<220000:break
 b=out.getvalue();return {'name':'fiche-'+hashlib.sha256(b).hexdigest()[:20]+'.webp','bytes':b,'width':im.width,'height':im.height}
def recover(row):
 urls=sources(row);photos=[]
 for i in range(row['count']):
  for attempt in range(4):
   try:p=optimize(get(urls[i]));p['alt']=row['alts'][i];assert len(p['alt'].strip())>5;photos.append(p);break
   except Exception:
    if attempt==3:raise
    urls=sources(row)
 return row,photos
def protected(d):
 return {'h1':d.xpath('//h1//text()'),'nav':[etree.tostring(n) for n in d.xpath('//nav')],'footer':[etree.tostring(n) for n in d.xpath('//footer')],'frames':[etree.tostring(n) for n in d.xpath('//iframe')],'ids':d.xpath('//*[@id]/@id'),'editorial':[' '.join(t.split()) for t in d.xpath('//main//text()[not(ancestor::figure)]') if t.strip()]}
def restore(content,photos,prefix):
 d=html.fromstring(content);before=protected(d);imgs=d.xpath('//main//img');assert len(imgs)==1
 fig=imgs[0].xpath('ancestor::figure[1]')[0];stack=html.Element('div',{'class':'photo-stack restored-fiche-photos'})
 for p in photos:
  f=html.Element('figure',{'class':'page-photo'});im=html.Element('img',{'src':prefix+'assets/photos/'+p['name'],'alt':p['alt'],'width':str(p['width']),'height':str(p['height']),'loading':'lazy','decoding':'async'});f.append(im);c=html.Element('figcaption');c.text=p['alt'];f.append(c);stack.append(f)
 fig.getparent().replace(fig,stack);assert protected(d)==before;assert len(d.xpath('//main//img'))==len(photos);assert not d.xpath('//iframe[@src]')
 return '<!doctype html>\n'+html.tostring(d,encoding='unicode',method='html')
recovered=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 for f in concurrent.futures.as_completed([pool.submit(recover,r) for r in MANIFEST['pages']]):
  recovered.append(f.result());print('Recovered fiches:',len(recovered),'/',MANIFEST['expected_pages'],flush=True)
assert len(recovered)==MANIFEST['expected_pages'];assert sum(len(p) for _,p in recovered)==MANIFEST['expected_photos']
# Write only after every original photo has been recovered.
for row,photos in recovered:
 for prefix in PREFIXES:
  for p in photos:
   asset=safe(prefix+'assets/photos/'+p['name']);asset.parent.mkdir(parents=True,exist_ok=True);asset.write_bytes(p['bytes'])
  page=safe(prefix+row['path']);urlprefix='/' if not prefix else '/banniere-nyons/vivreanyons-test/'
  page.write_text(restore(page.read_text('utf8'),photos,urlprefix),encoding='utf8')
for prefix in PREFIXES:
 css=safe(prefix+'assets/style.css');text=css.read_text('utf8');assert 'restored-fiche-photos' not in text
 css.write_text(text+'\n/* Complete original fiche photographs: preserve every image without cropping. */\n.restored-fiche-photos img{max-height:none;object-fit:contain}\n',encoding='utf8')
 js=safe(prefix+'assets/agenda.js');text=js.read_text('utf8');text=text.replace("  const figures=[...document.querySelectorAll('main figure')];\n  figures.slice(2).forEach(f=>f.remove());\n",'');assert 'figures.slice(2)' not in text;js.write_text(text,encoding='utf8')
# Verify all restored sources are local and every alt, image file and dimension exists.
for row,_ in recovered:
 for prefix in PREFIXES:
  d=html.fromstring(safe(prefix+row['path']).read_text('utf8'));imgs=d.xpath('//main//img');assert len(imgs)==row['count']
  for im in imgs:
   assert im.get('alt','').strip();asset=safe(prefix+'assets/photos/'+Path(im.get('src')).name);assert asset.is_file();assert Image.open(asset).size==(int(im.get('width')),int(im.get('height')))
print(json.dumps({'fiches':len(recovered),'photos':sum(len(p) for _,p in recovered),'added':MANIFEST['added_photos'],'alts_missing':0,'verified':True}))

"""Render only the existing Autour de Nyons portal, from local published pages.

Curated URLs are mandatory. New indexable articles under the same rubric are
discovered through the root sitemap. No network, AI, article edits or redirects.
"""
from pathlib import Path
from urllib.parse import urlsplit,unquote
from html.parser import HTMLParser
import argparse,html,json,re,unicodedata,xml.etree.ElementTree as ET
SITE='https://www.vivreanyons.fr';ROOT=Path(__file__).resolve().parents[1]
def plain(s):return ' '.join(s.split())
def normalized(s):return ''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if not unicodedata.combining(c))
class Metadata(HTMLParser):
 def __init__(self,source):
  super().__init__();self.data={};self.heading=False;self.title=False;self.h=[];self.t=[];self.images=[];self.feed(source)
  self.data['title']=plain(''.join(self.h) or ''.join(self.t))
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if t=='h1':self.heading=True
  if t=='title':self.title=True
  if t=='meta' and a.get('name') in ['description','robots']:self.data[a['name']]=a.get('content','')
  if t=='link' and a.get('rel')=='canonical':self.data['canonical']=a.get('href','')
  if t=='img' and a.get('src','').startswith('/assets/photos/'):self.images.append(a)
 def handle_endtag(self,t):
  if t=='h1':self.heading=False
  if t=='title':self.title=False
 def handle_data(self,s):
  if self.heading:self.h.append(s)
  if self.title:self.t.append(s)
def file_for(root,url):
 if not url.startswith('/') or not url.endswith('/') or '?' in url or '#' in url:raise ValueError('Invalid page URL '+url)
 p=(root/unquote(url).lstrip('/')/'index.html').resolve()
 if not p.is_relative_to(root.resolve()) or not p.is_file():raise ValueError('Missing article '+url)
 return p
def classify(title):
 t=normalized(title)
 if re.search(r'baign|fraicheur|gorges|cascade',t):return 'fraicheur'
 if re.search(r'chateau|palais|patrimoine|sculpt|vendangeuse',t):return 'patrimoine'
 if re.search(r'famill|enfant|ferme|observatoire|insolite|aquatique|ferrata',t):return 'famille'
 if re.search(r'marche|terroir|cave|vin|distiller',t):return 'terroir'
 if re.search(r'randon|nature|lavande|paysage|vautour|parc|soleil|vtt',t):return 'nature'
 return 'villages'
def collect(root,cfg):
 entries=[];seen=set()
 for e in cfg['entries']:
  file_for(root,e['url']);entries.append(dict(e));seen.add(e['url'])
 if not set(cfg['original_urls']).issubset(seen):raise ValueError('An original link was removed from the catalogue')
 urls=[n.text for n in ET.parse(root/'sitemap.xml').findall('.//{*}loc') if n.text]
 for full in urls:
  u=urlsplit(full);url=u.path
  if u.netloc!='www.vivreanyons.fr' or url in seen or url==cfg['portal'] or not url.startswith(cfg['portal']):continue
  try:p=file_for(root,url)
  except ValueError:continue
  m=Metadata(p.read_text(encoding='utf8'));data=m.data
  if data.get('canonical')!=SITE+url or 'noindex' in data.get('robots','').lower():continue
  im=next((a for a in m.images if (root/a['src'].lstrip('/')).is_file()),None)
  if im:im={'src':im['src'],'alt':im.get('alt') or data['title'],'width':int(im.get('width') or 600),'height':int(im.get('height') or 400)}
  entries.append({'url':url,'title':data['title'],'description':data.get('description') or 'Consultez les informations de cette nouvelle fiche pour préparer votre découverte.','group':classify(data['title']),'seasons':[],'image':im});seen.add(url)
 if len(entries)!=len(seen):raise ValueError('Duplicate article URL')
 return entries
def image(e,featured=False):
 im=e.get('image')
 if not im:return '<div class="ap-no-photo"><span>GUIDE PRATIQUE</span><strong>'+html.escape(e['title'])+'</strong></div>'
 return '<img src="'+html.escape(im['src'],quote=True)+'" width="'+str(im['width'])+'" height="'+str(im['height'])+'" alt="'+html.escape(im['alt'],quote=True)+'" loading="lazy" decoding="async">'
def card(e,cfg,featured=False):
 label=next(g['label'] for g in cfg['groups'] if g['id']==e['group'])
 attrs='' if featured else ' data-autour-card data-group="'+e['group']+'" data-seasons="'+' '.join(e['seasons'])+'" data-search="'+html.escape(e['title']+' '+e['description'],quote=True)+'"'
 return '<article class="ap-card"'+attrs+'><a href="'+html.escape(e['url'],quote=True)+'">'+image(e,featured)+'<div class="ap-card-copy"><span class="ap-eyebrow">'+html.escape(label)+'</span><h3>'+html.escape(e['title'])+'</h3><p>'+html.escape(e['description'])+'</p><span class="ap-card-cta">Préparer cette sortie <span aria-hidden="true">↗</span></span></div></a></article>'
def render(template,entries,cfg):
 by_url={e['url']:e for e in entries};groups=[]
 for g in cfg['groups']:
  selected=[e for e in entries if e['group']==g['id']]
  content='<section class="ap-group" id="'+g['id']+'" data-autour-group><div class="ap-group-heading"><span class="ap-group-icon" aria-hidden="true">'+g['icon']+'</span><div><h2>'+html.escape(g['heading'])+'</h2><p>'+html.escape(g['description'])+'</p></div></div><div class="ap-grid">'+''.join(card(e,cfg) for e in selected)+'</div></section>'
  groups.append(content)
 schema={'@context':'https://schema.org','@graph':[{'@type':'CollectionPage','@id':SITE+cfg['portal'],'url':SITE+cfg['portal'],'name':'Que faire autour de Nyons ? Les plus belles sorties en Drôme provençale','description':'Villages, nature, marchés et découvertes autour de Nyons.','inLanguage':'fr-FR','mainEntity':{'@id':SITE+cfg['portal']+'#sorties'}},{'@type':'ItemList','@id':SITE+cfg['portal']+'#sorties','numberOfItems':len(entries),'itemListElement':[{'@type':'ListItem','position':n,'item':{'@type':'WebPage','@id':SITE+e['url'],'url':SITE+e['url'],'name':e['title']}} for n,e in enumerate(entries,1)]},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':n,'name':name,'item':url} for n,(name,url) in enumerate([('Accueil',SITE+'/'),('Que faire à Nyons',SITE+'/que-faire-nyons/'),('Autour de Nyons',SITE+cfg['portal'])],1)]}]}
 parts={'@@CATALOGUE@@':''.join(groups),'@@FEATURED@@':''.join(card(by_url[u],cfg,True) for u in cfg['featured']),'@@SCHEMA@@':json.dumps(schema,ensure_ascii=False).replace('</','<\\/'),'@@COUNT@@':str(len(entries))}
 for token,value in parts.items():template=template.replace(token,value)
 if re.search(r'@@[A-Z_]+@@',template):raise ValueError('Unfilled template token')
 return template
def update(root=ROOT,check=False):
 root=Path(root);cfg=json.loads((root/'tools/autour-nyons.json').read_text(encoding='utf8'));target=file_for(root,cfg['portal']);entries=collect(root,cfg);template=(root/'tools/templates/autour-nyons.html.tpl').read_text(encoding='utf8');result=render(template,entries,cfg);old=target.read_text(encoding='utf8')
 if check and result!=old:raise ValueError('Autour portal needs regeneration')
 if not check and result!=old:target.write_text(result,encoding='utf8')
 print(f'Autour de Nyons: {len(entries)} unique guides; all {len(cfg["original_urls"])} original URLs retained.')
 return entries
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--check',action='store_true');a=p.parse_args();update(a.root,a.check)

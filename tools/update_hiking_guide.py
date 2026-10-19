"""Build this existing guide, its points and CSV from one reviewed local source.
No network calls, publishing, invented values, or writes to other articles.
"""
from pathlib import Path
import json,html,csv,io,hashlib,argparse,re
ROOT=Path(__file__).resolve().parents[1];SITE='https://www.vivreanyons.fr'
def escape(s):return html.escape(str(s),quote=True)
def distance(r):
 a,b=r['distance_km_min'],r['distance_km_max'];return (str(a).replace('.',',') if a==b else str(a).replace('.',',')+' à '+str(b).replace('.',','))+' km'
def minutes(n):return (str(n//60)+' h'+(' '+str(n%60).zfill(2) if n%60 else '')) if n>=60 else str(n)+' min'
def duration(r):return minutes(r['duration_min']) if r['duration_min']==r['duration_max'] else minutes(r['duration_min'])+' à '+minutes(r['duration_max'])
def card(r):
 image=r.get('image');picture='<img src="'+escape(image['src'])+'" width="'+str(image['width'])+'" height="'+str(image['height'])+'" alt="'+escape(image['alt'])+'" loading="lazy" decoding="async">' if image else '<div class="hg-no-photo"><span>DÉPART '+str(r['number']).zfill(2)+'</span><strong>'+escape(r['start'])+'</strong></div>'
 osm=f'https://www.openstreetmap.org/?mlat={r["lat"]}&mlon={r["lon"]}#map=17/{r["lat"]}/{r["lon"]}'
 parking=escape(r['parking'] or 'Aucun parking précis confirmé pour ce départ.')
 return f'''<article class="hg-card" id="rando-{r['id']}" data-hike-id="{r['id']}" data-difficulty="{r['difficulty']}" data-duration="{r['duration_max']}" data-distance="{r['distance_km_max']}" data-type="{r['route_type']}" data-family="{str(r['family_documented']).lower()}" data-commune="{escape(r['commune'])}" data-search="{escape(r['name']+' '+r['start']+' '+r['commune'])}">
 <div class="hg-card-visual">{picture}<span class="hg-number">{r['number']:02}</span><span class="hg-level {r['difficulty']}">{escape(r['difficulty_label'])}</span></div>
 <div class="hg-card-body"><span class="hg-kicker">{escape(r['commune'])} · {'Aller-retour' if r['route_type']=='aller-retour' else 'Boucle'}</span><h3><a href="{escape(r['article'])}">{escape(r['name'])}</a></h3><p>{escape(r['description'])}</p>
 <dl class="hg-facts"><div><dt>À pied</dt><dd>{distance(r)}</dd></div><div><dt>Durée</dt><dd>{duration(r)}</dd></div><div><dt>Dénivelé</dt><dd>+ {r['ascent_m']} m</dd></div></dl>
 <details><summary>Départ, parking et précisions</summary><p><strong>Départ pédestre :</strong> {escape(r['start'])}.</p><p><strong>Stationnement :</strong> {parking} Les places, l’accès et les règles du jour restent à confirmer. Le marqueur indique le départ à pied.</p><p>{escape(r['note'])}</p><p><a href="{escape(r['source'])}">Source officielle</a> · Vérification documentaire du 19 octobre 2026.</p></details>
 <div class="hg-card-actions"><a class="hg-button" href="{escape(r['article'])}">Lire le guide</a><button type="button" data-locate="{r['id']}" hidden>Voir le départ</button><a href="{escape(r['gpx'])}">GPX officiel ↗</a><a href="{escape(osm)}">Localiser le départ ↗</a></div></div></article>'''
def generate(root=ROOT,check=False):
 root=Path(root);cfg=json.loads((root/'tools/randonnees-nyons.json').read_text(encoding='utf8'));rows=cfg['rows'];assert len({r['id'] for r in rows})==len(rows)
 for r in rows:
  assert r['verification_method']=='documentaire_sans_controle_terrain'
  assert r['point_type']=='depart_pedestre' and 44<r['lat']<45 and 4<r['lon']<6
  assert (root/r['article'].lstrip('/')/'index.html').is_file(),'Missing existing guide '+r['article']
  assert r['duration_min']<=r['duration_max'] and r['distance_km_min']<=r['distance_km_max']
  assert r['parking_lat'] is None and r['parking_lon'] is None,'Separate parking verification needed'
 page=SITE+cfg['page'];graph={'@context':'https://schema.org','@graph':[{'@type':'CollectionPage','@id':page,'url':page,'name':'Randonnées autour de Nyons : carte des départs et plus belles balades','inLanguage':'fr-FR','mainEntity':{'@id':page+'#circuits'}},{'@type':'ItemList','@id':page+'#circuits','numberOfItems':len(rows),'itemListElement':[{'@type':'ListItem','position':i,'name':r['name'],'url':SITE+r['article']} for i,r in enumerate(rows,1)]},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i,'name':name,'item':url} for i,(name,url) in enumerate([('Accueil',SITE+'/'),('Que faire à Nyons',SITE+'/que-faire-nyons/'),('Randonnées autour de Nyons',page)],1)]}]}
 template=(root/'tools/templates/randonnees-guide.html.tpl').read_text(encoding='utf8')
 values={'@@CARDS@@':''.join(card(r) for r in rows),'@@SCHEMA@@':json.dumps(graph,ensure_ascii=False).replace('</','<\\/'),'@@DATA@@':json.dumps(rows,ensure_ascii=False).replace('</','<\\/'),'@@COUNT@@':str(len(rows)),'@@COMMUNES@@':''.join('<option value="'+escape(c)+'">'+escape(c)+'</option>' for c in sorted({r['commune'] for r in rows}))}
 for token,value in values.items():template=template.replace(token,value)
 assert not re.search(r'@@[A-Z_]+@@',template)
 points={'type':'FeatureCollection','name':'Départs pédestres documentés autour de Nyons','license':'Licence Ouverte / Open Licence 2.0','verification_date':'2026-10-19','verification_scope':'documentaire, sans validation terrain ou ouverture garantie','features':[{'type':'Feature','id':r['id'],'geometry':{'type':'Point','coordinates':[r['lon'],r['lat']]},'properties':{**{k:v for k,v in r.items() if k not in ['image','lat','lon']},'url_fiche':SITE+r['article'],'latitude_depart':r['lat'],'longitude_depart':r['lon']}} for r in rows]}
 fields=['id','nom','commune','departement','latitude_depart','longitude_depart','type_point','depart','parking','statut_parking','latitude_parking','longitude_parking','distance_km_min','distance_km_max','duree_min_minutes','duree_max_minutes','denivele_positif_m','difficulte','type_circuit','famille_documentee','url_fiche','url_gpx','url_source','sources_complementaires','date_verification_documentaire','ouverture']
 buffer=io.StringIO(newline='');writer=csv.writer(buffer,lineterminator='\r\n');writer.writerow(fields)
 for r in rows:writer.writerow([r['id'],r['name'],r['commune'],r['departement'],r['lat'],r['lon'],r['point_type'],r['start'],r['parking'],r['parking_status'],r['parking_lat'],r['parking_lon'],r['distance_km_min'],r['distance_km_max'],r['duration_min'],r['duration_max'],r['ascent_m'],r['difficulty'],r['route_type'],str(r['family_documented']).lower(),SITE+r['article'],r['gpx'],r['source'],' '.join(r['source_details']),r['verification_date'],r['opening_status']])
 files={cfg['page'].lstrip('/')+'index.html':template,'assets/randonnees-guide/departs.geojson':json.dumps(points,ensure_ascii=False,indent=2)+'\n','assets/randonnees-guide/randonnees-verifiees.csv':buffer.getvalue()}
 for name,text in files.items():
  p=root/name;p.parent.mkdir(parents=True,exist_ok=True);data=text.encode('utf8')
  if check:assert p.read_bytes()==data,'Generation required: '+name
  elif not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
 print(f'{len(rows)} documented circuits, {len(points["features"])} departure points; no parking coordinates or route geometries invented.')
 return files
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--check',action='store_true');a=p.parse_args();generate(a.root,a.check)

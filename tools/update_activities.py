"""Render only /que-faire-nyons/ from its curated activity catalogue.

No network request, page creation, sitemap or global SEO update. The existing
header, footer and article destinations are retained. --check verifies stability.
"""
from pathlib import Path
from urllib.parse import urljoin
import argparse,html,json,re
import harmonize_seo
ROOT=Path(__file__).resolve().parents[1]
URL='https://www.vivreanyons.fr/que-faire-nyons/'
PAGE=ROOT/'que-faire-nyons/index.html'
LABELS={'sport':'Sports','balade':'Balades','patrimoine':'Patrimoine','culture':'Culture','terroir':'Terroir'}
FAQ=[
 ('Comment rechercher une activité à Nyons ?', 'Tape une envie, comme boules, marcher, piscine ou olives. Tu peux combiner le mot recherché avec une catégorie, un lieu et plusieurs filtres. Effacer les filtres rétablit toutes les activités.'),
 ('Que signifient les filtres Gratuit et Quand il pleut ?', 'Gratuit retient une formule gratuite identifiée dans la fiche, avec ses conditions : cela ne couvre pas tous les achats, groupes ou ateliers. Quand il pleut propose des visites à l’abri, pendant leurs horaires d’accueil.'),
 ('Comment choisir une sortie avec des enfants ou des seniors ?', 'Les sélections Enfants et Seniors donnent des pistes, pas une garantie pour chaque âge ou chaque mobilité. Vérifie les conditions, les escaliers et la longueur de la promenade dans la fiche avant de partir.'),
 ('Où trouver les concerts et événements à venir ?', 'L’agenda de Vivre à Nyons rassemble les rendez-vous datés. Ce moteur présente des activités et des lieux permanents, dont le cinéma L’Arlequin, sans ajouter les séances ordinaires à ses résultats.')]
def esc(s):return html.escape(str(s),quote=True)
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s))).strip()
def render(source,data):
 title='Que faire à Nyons ? Activités, visites et sorties'
 desc='Trouvez une activité à Nyons : visites, sports, balades, sorties en famille, idées gratuites ou à l’abri, avec des filtres et des liens pratiques.'
 source=re.sub(r'<title>.*?</title>','<title>'+title+'</title>',source,count=1,flags=re.S)
 source=re.sub(r'(<meta (?:name="description"|property="og:description") content=")[^"]*(")',lambda m:m[1]+esc(desc)+m[2],source)
 source=re.sub(r'(<meta property="og:title" content=")[^"]*(")',lambda m:m[1]+esc(title)+m[2],source)
 source=re.sub(r'<h1>.*?</h1>','<h1>'+title+'</h1>',source,count=1,flags=re.S)
 source=re.sub(r'(activities-nyons\.(?:css|js)\?v=)[^" ]+',r'\g<1>20261023-2',source)
 intro='<div class="activity-intro"><p>À Nyons, on ne manque pas de choses à faire. Mais encore faut-il savoir où chercher !</p></div>'
 head='''<section class="activity-search" aria-labelledby="activity-search-title" data-activity-search>
<h2 id="activity-search-title">Trouve ta prochaine sortie</h2><p id="activity-search-help"><strong>Tape simplement ce que tu cherches, ou choisis une catégorie.</strong></p>
<form role="search" aria-label="Rechercher une activité à Nyons" hidden><div class="activity-fields">
<div><label for="activity-query">Quelle activité ?</label><input id="activity-query" type="search" placeholder="Ex. boules, marcher, olives…" autocomplete="off" aria-describedby="activity-search-help" aria-controls="activity-results"></div>
<div><label for="activity-category">Catégorie</label><select id="activity-category" aria-controls="activity-results"><option value="">Toutes les catégories</option>'''+''.join('<option value="'+k+'">'+v+'</option>' for k,v in LABELS.items())+'''</select></div>
<div><label for="activity-zone">Où ?</label><select id="activity-zone" aria-controls="activity-results"><option value="">Nyons et alentours</option><option value="nyons">Nyons uniquement</option><option value="autour">Autour de Nyons</option></select></div></div>
<fieldset class="activity-facets"><legend>Mes envies — filtres combinables</legend>'''+''.join('<label><input type="checkbox" name="facet" value="'+k+'" aria-controls="activity-results"> '+v+'</label>' for k,v in [('famille','Enfants'),('senior','Seniors'),('gratuit','Gratuit'),('pluie','Quand il pleut')])+'''</fieldset><button type="reset">Effacer les filtres</button></form>
<div class="activity-shortcuts" aria-label="Idées de recherches" data-activity-shortcuts hidden>'''+''.join('<button type="button" data-activity-query="'+esc(q)+'">'+esc(q)+'</button>' for q in ['Tennis','Pétanque','Randonnée','Cinéma','Olives','Piscine'])+'''</div>
<p class="activity-more"><a href="https://agenda.vivreanyons.fr/">Les événements datés dans l’agenda ↗</a> · <a href="#fiches-que-faire">Nos guides complémentaires ↓</a></p><p class="activity-status" role="status" aria-live="polite" aria-atomic="true" hidden></p><p class="activity-selection-note">Gratuit : une formule vérifiée, selon les conditions de la fiche. Seniors : idées de sorties tranquilles, sans garantie d’accessibilité. Les ouvertures restent à vérifier avant de venir.</p>
<details id="activity-results" open><summary>Parcourir les '''+str(len(data))+''' activités</summary><ul class="activity-list" data-activity-list>'''
 cards=[]
 for x in data:
  cats=' · '.join(LABELS[k] for k in x['categories']);facets=' '.join(x['facets'])
  cards.append('<li data-activity data-categories="'+esc(' '.join(x['categories']))+'" data-facets="'+esc(facets)+'" data-zone="'+x['zone']+'" data-keywords="'+esc(x['keywords'])+'"><article class="card activity-card"><span class="activity-meta">'+esc(cats)+' · '+esc(x['commune'])+(' · Autour de Nyons' if x['zone']=='autour' else '')+'</span><h3><a href="'+esc(x['url'])+'">'+esc(x['title'])+'</a></h3><p>'+esc(x['description'])+'</p><p class="activity-practical">'+esc(x['practical'])+'</p></article></li>')
 tail='''</ul><p data-activity-empty hidden>Aucune activité ne correspond à ces filtres. Essaie un mot plus simple ou utilise « Effacer les filtres ». Pour une sortie à une date précise, consulte <a href="https://agenda.vivreanyons.fr/">l’agenda</a>.</p><p class="activity-display" data-activity-display hidden></p><button type="button" data-activity-more hidden>Afficher 8 activités de plus</button></details>
<noscript><p>Sans JavaScript, les '''+str(len(data))+''' fiches et leurs liens sont disponibles ci-dessus. Les filtres nécessitent JavaScript ; utilise la recherche de ton navigateur pour retrouver un mot.</p></noscript></section>'''
 closing='''<div class="activity-intro activity-afterword"><p>Une partie de pétanque sur la place, une balade entre les oliviers, une visite de la Scourtinerie, un après-midi avec les enfants ou simplement une flânerie dans les vieilles ruelles : les occasions de sortir ne manquent pas à Nyons.</p><p>J'ai voulu rassembler ici les bonnes idées de sorties de la ville, dans un seul endroit. Que vous habitiez le coin depuis toujours ou que vous soyez de passage, vous devriez y trouver votre compte.</p><p>Notre moteur vous proposera les activités qui correspondent à ce que vous cherchez, avec les informations pratiques (horaires, tarifs, accès) et un lien pour en savoir plus.</p><p>Et si vous ne savez pas encore quoi faire, jetez un œil aux suggestions : il y a parfois de belles découvertes à deux pas de chez nous, sans avoir besoin d'aller bien loin.</p><p><em>Le petit conseil de Papy Chris ❤️ : inutile de prévoir dix visites dans la même journée. À Nyons, prendre son temps fait aussi partie du plaisir !</em></p></div>'''
 # Replace the existing engine in place, retaining the common shell.
 source=re.sub(r'<!-- activity-search:start -->.*?<!-- activity-search:end -->', '<!-- activity-search:start -->'+intro+head+'\n'.join(cards)+tail+closing+'<!-- activity-search:end -->',source,flags=re.S)
 source=source.replace('<p>Retrouve ici toutes les fiches de la rubrique que faire à nyons.</p>','')
 # Legacy article links are moved, not deleted. Indexed activities appear once.
 # On subsequent runs, the generated supplementary section is retained unchanged.
 grid=re.search(r'<section class="grid" id="fiches-que-faire">(.*?)</section>',source,re.S)
 if grid:
  indexed={x['url'] for x in data};groups={'Guides pour préparer son séjour':[],'Patrimoine et autres regards':[],'Eau, nature et promenades':[],'Culture, terroir et savoir-faire':[]}
  extras=[x for x in before_guides() if x['url'] not in indexed]
  seen=set()
  raw=[]
  for block in re.findall(r'<article\b.*?</article>',grid[1],re.S):
   m=re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>',block,re.S)
   if m:raw.append((html.unescape(m[1]),clean(m[2])))
  raw += [(x['url'],x['title']) for x in extras]
  for u,t in raw:
   if u in indexed or u in seen:continue
   seen.add(u);low=u.lower()
   if any(z in low for z in ['baign','aquatique','eygue','randonn','courir','spots']):g='Eau, nature et promenades';note='Repères et conseils à consulter avant la sortie.'
   elif any(z in low for z in ['moulin','distillerie','oliv','artiste','atelier','ferme','agenda']):g='Culture, terroir et savoir-faire';note='Informations complémentaires et conditions à consulter dans le guide.'
   elif any(z in low for z in ['tour-randonne','ruelles','chateau','que-voir']):g='Patrimoine et autres regards';note='Histoire, photographies et conseils de découverte.'
   else:g='Guides pour préparer son séjour';note='Un guide pour organiser tes visites selon tes envies.'
   groups[g].append('<li><a href="'+esc(u)+'">'+esc(t)+'</a><p>'+note+'</p></li>')
  supplementary='<section class="activity-reading" id="fiches-que-faire"><h2>Pour aller plus loin : nos guides et récits</h2><p>Les activités sont dans le moteur ci-dessus. Ces lectures complémentaires permettent de préparer un séjour ou de découvrir un autre regard sur un lieu.</p>'+''.join('<details><summary>'+g+' ('+str(len(items))+')</summary><ul>'+''.join(items)+'</ul></details>' for g,items in groups.items() if items)+'</section>'
  source=source[:grid.start()]+supplementary+source[grid.end():]
 # Remove the old dynamic agenda teaser: all dated content has a distinct access.
 source=re.sub(r'<section class="agenda">.*?</section>','',source,flags=re.S)
 agenda='<section class="activity-agenda" id="sorties-datees"><h2>Une sortie aujourd’hui ou ce week-end ?</h2><p>Pour les concerts, fêtes, expositions et autres rendez-vous datés, <a href="https://agenda.vivreanyons.fr/">ouvre l’agenda de Nyons</a>. Ici, tu retrouves les activités et les lieux, sans liste de séances ordinaires de cinéma.</p></section>'
 faq='<section class="activity-faq" id="questions-activites"><h2>Questions / réponses</h2>'+''.join('<details><summary>'+esc(q)+'</summary><p>'+esc(a)+'</p></details>' for q,a in FAQ)+'</section>'
 sources='<section class="activity-sources"><h2>Sources et liens utiles</h2><p>Sélection vérifiée le 23 octobre 2026 à partir des fiches liées. Pour les balades, consulte le départ, la difficulté et les conditions du jour avant de partir.</p><ul><li><a href="https://www.nyons.com/vivre-nyons/culture-et-loisirs/sentiers-decouverte/">Sentiers découverte de la Ville de Nyons</a></li><li><a href="https://www.vignolis.fr/fr/espace-vignolis/musee">Vignolis : gratuité de la visite libre du musée</a></li><li><a href="https://huilerie-richard.com/nos-moulins/moulin-de-nyons/">Moulin Richard : visites et accueil</a></li><li><a href="/que-faire-nyons/randonnees-autour-de-nyons-carte/">Carte et précisions sur les parcours documentés</a></li><li><a href="/a-faire-autour-de-Nyons/">Préparer d’autres escapades autour de Nyons</a></li></ul></section>'
 source=re.sub(r'<section class="activity-agenda".*?</section>','',source,flags=re.S)
 source=re.sub(r'<section class="activity-faq".*?</section>','',source,flags=re.S)
 source=re.sub(r'<section class="activity-sources".*?</section>','',source,flags=re.S)
 source=source.replace('</main>',agenda+faq+sources+'</main>',1)
 source=re.sub(r'<script data-activity-schema="v1".*?</script>','',source,flags=re.S)
 graph=[{'@type':'ItemList','@id':URL+'#items','numberOfItems':len(data),'itemListElement':[{'@type':'ListItem','position':i+1,'item':{'@type':'WebPage','@id':urljoin(URL,x['url']),'url':urljoin(URL,x['url']),'name':x['title']}} for i,x in enumerate(data)]},{'@type':'FAQPage','@id':URL+'#questions-activites','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in FAQ]}]
 source=source.replace('</head>','<script data-activity-schema="v1" type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False).replace('</',r'<\/')+'</script></head>',1)
 config=json.loads((ROOT/'tools/seo-policy.json').read_text(encoding='utf-8'))
 source,_=harmonize_seo.optimize(source,URL,config,{URL:source})
 return source
def before_guides():
 return [dict(title=t,url=u) for t,u in [('Clubs sportifs de Nyons — annuaire et carte','/nyons-carte-interactive/sport--nyons/#sports-directory-title'),('Course à pied et trail autour de Nyons','/que-faire-nyons/courir-a-nyons/'),('Artistes et artisans d’art à Nyons','/que-faire-nyons/artistes-artisans-art-nyons/'),('Nyons avec des enfants — idées en famille','/que-faire-nyons/nyons-avec-des-enfants/')]]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 source=PAGE.read_text(encoding='utf-8');data=json.loads((ROOT/'tools/activities-nyons.json').read_text(encoding='utf-8'))
 assert len({x['url'] for x in data})==len(data),'Duplicate activity'
 rendered=render(source,data)
 assert render(rendered,data)==rendered,'Unstable generation'
 if args.check:
  assert source==rendered,'Page needs regeneration'
 else:PAGE.write_text(rendered,encoding='utf-8',newline='')
 print(str(len(data))+' activities; page '+('stable' if args.check else 'rendered'))
if __name__=='__main__':main()

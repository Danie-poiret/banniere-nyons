'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {createRequire}=require('node:module');
const req=createRequire(path.join(__dirname,'layout/package.json'));
const {parseHTML}=req('linkedom');
const {render}=require('./stabilize_layout.cjs');
const SITE='https://www.vivreanyons.fr';
const existing=['/que-faire-nyons/Pont-Roman-de-Nyons/','/que-faire-nyons/parc-aquatique-nyons/','/infos-pratiques-nyons/petanque-nyons/','/infos-pratiques-nyons/ressourceries-de-nyons/','/que-faire-nyons/Marche-de-Nyons/','/evenements-nyons/8-jours-de-petanque-de-Nyons/'];
function fixture(route,title){return '<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>'+title+'</title><link rel="canonical" href="'+SITE+route+'"><meta name="description" content="Description originale"><script type="application/ld+json">{"@type":"Article","headline":"Titre original"}</script></head><body><header><nav class="nav"><a class="brand" href="/">Nyons</a><div class="navlinks"><a href="/">Accueil</a><details class="rubriques"><summary>Rubriques</summary><div class="rubriques-menu"></div></details></div></nav></header><section class="hero"><h1>'+title+'</h1></section><main><article><p>Un récit original avec ses anecdotes.</p><a href="/infos-pratiques-nyons/fabrique-nyons/">La Fabrique</a><img src="/original.webp" width="900" height="600" alt="Photo originale"></article><aside class="right-sidebar"><section class="side-card"><div class="side-title">Menu existant</div><nav class="side-links">'+existing.map(u=>'<a href="'+u+'">Lien conservé</a>').join('')+'</nav></section></aside></main><script src="/assets/agenda.js"></script></body></html>';}
const samples=[
 ['/que-faire-nyons/Pont-Roman-de-Nyons/','Pont Roman de Nyons'],
 ['/infos-pratiques-nyons/bivouak-nyons/','Bivouak à Nyons : bières artisanales'],
 ['/infos-pratiques-nyons/fabrique-nyons/','La Fabrique, ressourcerie à Nyons'],
 ['/infos-pratiques-nyons/cinema-nyons/','Cinéma L’Arlequin à Nyons'],
 ['/infos-pratiques-nyons/dentistes-nyons/','Dentistes à Nyons'],
 ['/infos-pratiques-nyons/portail-famille-nyons/','Portail Famille Nyons'],
 ['/infos-pratiques-nyons/petanque-nyons/','Pétanque à Nyons'],
 ['/restaurants-de-nyons/le-bistrotteur-nyons/','Le Bistrotteur à Nyons'],
 ['/a-faire-autour-de-Nyons/avis-gorges-du-toulourenc/','Gorges du Toulourenc'],
 ['/a-faire-autour-de-Nyons/thermes-montbrun-les-bains/','Thermes de Montbrun-les-Bains en couple'],
 ['/ou-dormir-a-nyons/camping/','Choisir un camping à Nyons']
];
const selections=[];
for(const[route,title]of samples){
 const source=fixture(route,title),result=render(source,SITE+route),{document}=parseHTML(result);
 const card=document.querySelector('[data-nyons-related-links]');assert(card,'Missing card '+route);
 const links=[...card.querySelectorAll('a')];assert.equal(links.length,3,route);
 const urls=links.map(a=>a.getAttribute('href'));assert.equal(new Set(urls).size,3);assert(!urls.includes(route));
 assert(urls.every(u=>!existing.includes(u)));assert(urls.every(u=>u.endsWith('/')));
 assert.equal(render(result,SITE+route),result,'Stable second render '+route);
 assert.equal(result.match(/<article>[\s\S]*?<\/article>/)[0],source.match(/<article>[\s\S]*?<\/article>/)[0]);
 for(const rx of [/<title>.*?<\/title>/,/<meta name="description"[^>]+>/,/<script type="application\/ld\+json">.*?<\/script>/])assert.equal(result.match(rx)[0],source.match(rx)[0]);
 selections.push({route,links:links.map(a=>({url:a.getAttribute('href'),label:a.textContent}))});
}
const foreignCatalog=[1,2,3,4].map(i=>['Hauts-de-France/Nord/Lille/recit-'+i+'/','region:Hauts-de-France/Nord,memoire,ville:lille',['Souvenirs de Lille '+i],true]);
const incoming=new Map(foreignCatalog.map(e=>['/'+e[0],0]));
for(const e of foreignCatalog){
 const route='/'+e[0],result=render(fixture(route,'Lille autrefois'),SITE+route,foreignCatalog),{document}=parseHTML(result);
 const links=[...document.querySelectorAll('[data-nyons-related-links] a')];assert.equal(links.length,3);
 for(const a of links){const u=a.getAttribute('href');assert(u.startsWith('/Hauts-de-France/Nord/Lille/'));assert.notEqual(u,route);incoming.set(u,incoming.get(u)+1);}
 assert.equal(render(result,SITE+route,foreignCatalog),result);
}
assert([...incoming.values()].every(n=>n>=1),'Each story has an incoming thematic link');
assert(new Set(selections.map(s=>JSON.stringify(s.links))).size>6,'Selections vary with the subject');
const outdoorFixture=fixture('/que-faire-nyons/exemple/','Visiter Nyons').replace('<nav class="side-links">','<nav class="side-links" aria-label="Plein air">').replace('<a href="/que-faire-nyons/parc-aquatique-nyons/">Lien conservé</a>','');
const outdoorResult=render(outdoorFixture,SITE+'/que-faire-nyons/exemple/');
assert(!parseHTML(outdoorResult).document.querySelector('[data-nyons-related-links] a[href="/que-faire-nyons/parc-aquatique-nyons/"]'),'Do not duplicate the pool link added by the shared menu');
const cultureSource=fixture('/que-faire-nyons/exemple/','Visiter Nyons').replace('</aside>','<nav class="side-links" aria-label="Culture"><a href="/que-faire-nyons/Tour-Randonne/">Tour</a><a href="/que-faire-nyons/Vieilles-ruelles-de-Nyons/">Vieux</a><a href="/que-faire-nyons/Pont-Roman-de-Nyons/">Pont</a></nav></aside>');
const cultureResult=render(cultureSource,SITE+'/que-faire-nyons/exemple/');
assert.deepEqual([...parseHTML(cultureResult).document.querySelectorAll('nav[aria-label="Culture"] a')].map(a=>a.textContent),['Vieux Nyons','Tour Randonne Nyons','Pont Roman Nyons']);
assert.equal(render(cultureResult,SITE+'/que-faire-nyons/exemple/'),cultureResult);
assert(!render(fixture('/Hauts-de-France/Nord/Lille/exemple/','Lille autrefois'),SITE+'/Hauts-de-France/Nord/Lille/exemple/',[]).includes('data-nyons-related-links'),'No unrelated Nyons filler when the history catalogue is empty');
if(process.env.NYONS_RELATED_REPORT)fs.writeFileSync(process.env.NYONS_RELATED_REPORT,JSON.stringify(selections,null,2));
console.log('11 local themes: three distinct links, unchanged URLs/article/SEO, no existing-menu duplicates, stable selection: OK');

'use strict';
const assert=require('node:assert/strict');
const {render}=require('./stabilize_layout.cjs');
function fixture(route,legacy=''){
 return '<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="canonical" href="https://www.vivreanyons.fr'+route+'"><script type="application/ld+json">{"@type":"Article","headline":"Souvenirs & mémoire"}</script></head><body><header><nav class="nav"><a class="brand" href="/">🌿 Vivre à Nyons ?</a><div class="navlinks"><a href="/">Accueil</a><details class="rubriques"><summary>Toutes les rubriques</summary><div class="rubriques-menu"></div></details></div></nav></header><section class="hero"><h1>Histoire et photographies</h1></section>'+legacy+'<main><article><p>Témoignage original : « Nyons, 1925 ».</p><img src="/photo-originale.png" width="960" height="676" alt="Photo historique"></article></main><script src="/assets/agenda.js"></script></body></html>';
}
for(const route of ['/que-faire-nyons/exemple/','/ou-dormir-a-nyons/exemple/','/ou-dormir-a-nyons/La-Lezardiere/','/Provence-Alpes-Cote-dAzur/Bouches-du-Rhone/Marseille/exemple/']){
 const source=fixture(route),result=render(source,'https://www.vivreanyons.fr'+route);
 assert.equal(render(result,'https://www.vivreanyons.fr'+route),result,'Idempotence: '+route);
 assert.equal(result.match(/<main>[\s\S]*?<\/main>/)[0],source.match(/<main>[\s\S]*?<\/main>/)[0]);
 assert(result.includes(source.match(/<script type="application\/ld\+json">[\s\S]*?<\/script>/)[0]));
 assert.equal((result.match(/data-nyons-lodging=""/g)||[]).length,1);
 if(route.includes('/La-Lezardiere/'))assert(!result.includes('data-nyons-partner-cards=""'));
 else assert.equal((result.match(/data-nyons-partner-cards=""/g)||[]).length,1);
 if(route.includes('/Marseille/'))assert(result.includes('marseille-book-banner'));
 if(route==='/ou-dormir-a-nyons/exemple/')assert(result.includes('nyons-partner-cards--stay'));
}
const legacy=fixture('/exemple/','<aside class="top"><iframe src="/banniere-livres/"></iframe></aside>');
assert(!render(legacy,'https://www.vivreanyons.fr/exemple/').includes('<iframe'));
assert.equal(render('<meta http-equiv="refresh" content="0;url=/">','https://www.vivreanyons.fr/ancien/'),'<meta http-equiv="refresh" content="0;url=/">');
assert.equal(render(fixture('/exemple/'),'https://www.vivreanyons.fr/alias/'),fixture('/exemple/'));
for(const nested of [false,true]){
 let source=fixture('/carte/').replace('<section class="hero"><h1>Histoire et photographies</h1></section>','');
 if(nested)source=source.replace('<main>','<main><section class="hero"><h1>Parcours</h1></section>');
 const result=render(source,'https://www.vivreanyons.fr/carte/');
 assert.equal(render(result,'https://www.vivreanyons.fr/carte/'),result);
 assert.equal(result.replace(/<!-- nyons-layout-partners:start -->[\s\S]*?<!-- nyons-layout-partners:end -->/, '').match(/<main>[\s\S]*?<\/main>/)[0],source.match(/<main>[\s\S]*?<\/main>/)[0]);
}
console.log('Layout variants, legacy banner replacement, unchanged articles/JSON-LD and idempotence: OK');

const assert=require('node:assert/strict'),fs=require('node:fs'),api=require('../assets/home.js');
const now=new Date('2026-10-10T14:00:00Z');
const base={url:'https://agenda.vivreanyons.fr/evenements/test/',title:'Test',kind:'event',start:'2026-10-10',end:'2026-10-10',startTime:'10:00',endTime:'12:00'};
assert.equal(api.select([base],now).length,0);
assert.equal(api.select([{...base,endTime:''}],now).length,1);
const film={...base,kind:'cinema',sessions:[{date:'2026-10-10',time:'12:00'},{date:'2026-10-10',time:'18:30'}]};
assert.equal(api.select([film],now)[0].startTime,'18:30');
assert.equal(api.select([film],new Date('2026-10-10T19:00:00Z')).length,0);
assert.deepEqual(api.weekend('2026-10-11'),['2026-10-10','2026-10-11']);
assert.equal(api.stamp(new Date('2026-10-10T23:30:00Z')).slice(0,10),'2026-10-11');
assert.equal(api.season('2026-12-01'),'winter');assert.equal(api.esc('<script>'),'&lt;script&gt;');
const page=fs.readFileSync('index.html','utf8');
assert(page.indexOf('data-nyons-lodging')<page.indexOf('<header>'));
const lodging=page.match(/<aside[^>]+data-nyons-lodging[\s\S]*?<\/aside>/)[0];
assert(lodging.includes('href="/demande-sejour-lezardiere/"'));
assert(lodging.includes('☀️ Prépare ton séjour à Nyons →'));
assert(!lodging.includes('wa.me/'));assert(!lodging.includes('06 32 07 61 24'));
assert.equal((page.match(/class="home-latest-card"/g)||[]).length,5);
assert(!page.includes('<p>Chargement…</p>'));assert(page.includes('data-nyons-weather'));assert(page.indexOf('data-nyons-weather')<page.indexOf('HOME_LATEST_START'));
// Editorial wording must not prevent the agenda HTML from being refreshed.
assert.match(page, /<h1\b[^>]*>[^<\s][^<]*<\/h1>/);
assert(page.includes('<title>Vivre à Nyons Drôme: guide local, sorties et bonnes adresses</title>'));
assert(page.includes('href="https://www.vivreanyons.fr/"'));
assert(!page.includes('data-agenda>'));assert.equal((page.match(/data-nyons-lodging\b/g)||[]).length,1);
console.log('Homepage dates, events, banner, metadata and weather: OK');
// Reading order and authored placements must survive every automated refresh.
const sections=['nyons-key-figures','nyons-presentation','aujourdhui-nyons','decouvrir-nyons','univers-olive-accueil','univers-lavande-accueil','environs-nyons','preparer-sejour','data-home-season','vie-quotidienne','histoire-memoire','derniers-articles','chiffres-nyons','rubriques'];
let previous=-1;
for(const id of sections){const at=page.indexOf(id==='data-home-season'?id:'id="'+id+'"');assert(at>previous,'Homepage order: '+id);previous=at;}
assert.equal((page.match(/data-nyons-partner="lezardiere"/g)||[]).length,1);
assert.equal((page.match(/data-nyons-partner="livres"/g)||[]).length,1);
assert(page.indexOf('id="preparer-sejour"')<page.indexOf('data-nyons-partner="lezardiere"'));
assert(page.indexOf('data-nyons-partner="lezardiere"')<page.indexOf('data-home-season'));
assert(page.indexOf('id="histoire-memoire"')<page.indexOf('data-nyons-partner="livres"'));
assert(page.indexOf('data-nyons-partner="livres"')<page.indexOf('id="derniers-articles"'));
console.log('Homepage hierarchy and contextual partner placements: OK');

assert(page.indexOf('id="nyons-key-figures"')<page.indexOf('class="home-jumps"'),'Key figures must precede homepage shortcuts');

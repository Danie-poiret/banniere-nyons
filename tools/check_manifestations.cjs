'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),a=require('../assets/manifestations.js');
const when=new Date('2026-10-23T18:30:00Z'); // 20:30 in Paris
const url=n=>`https://agenda.vivreanyons.fr/evenements/${n}/`;
const row=(title,start,extra={})=>({title,start_date:start,end_date:start,page_url:url(title),...extra});
const raw=[
  row('past','2026-10-22'),row('started','2026-10-23',{start_time:'20:00'}),row('later','2026-10-23',{start_time:'21:00'}),
  row('saturday','2026-10-24',{start_time:'10:00',categories:['Enfance / Jeunesse']}),
  row('sunday','2026-10-25'),row('monday','2026-10-26'),
  row('film','2026-10-21',{end_date:'2026-10-27',kind:'cinema',sessions:[{date:'2026-10-23',time:'17:00'},{date:'2026-10-24',time:'17:00'},{date:'2026-10-26',time:'19:00'}]}),
  row('ongoing-exposition','2026-10-20',{end_date:'2026-10-25',categories:['Exposition']}),
  row('ended-exposition','2026-10-20',{end_date:'2026-10-23',end_time:'18:00',categories:['Exposition']}),
  row('warning','2026-10-25',{date_warning:'Conflicting dates'}),row('unpublished','2026-10-25'),
  row('saturday','2026-10-24',{start_time:'10:00'}),
  row('elsewhere','2026-10-24',{commune:'Vinsobres'}),
  row('unknown-price','2026-10-25',{summary:'entrée libre'}),
  row('free','2026-10-25',{practical:{tarifs:'Entrée libre'}}),
  row('conditionally-free','2026-10-25',{practical:{tarifs:'10 €, gratuit pour les moins de 12 ans'}})
];
const published=raw.filter(x=>x.title!=='unpublished').map(x=>x.page_url);
const data={events:a.normalize({events:raw},published)};
const all=a.select(data,when);
assert(!all.upcoming.some(e=>['past','started','warning','unpublished','elsewhere'].includes(e.title)));
assert.equal(all.upcoming.filter(e=>e.title==='saturday').length,1);
assert.equal(all.ongoing.length,1);
assert.equal(all.upcoming.find(e=>e.title==='film').date,'2026-10-24');
assert.deepEqual(a.select(data,when,'today').upcoming.map(e=>e.title),['later']);
assert(a.select(data,when,'weekend').upcoming.every(e=>e.date>='2026-10-24'&&e.date<='2026-10-25'));
assert(!a.select(data,when,'week').upcoming.some(e=>e.title==='monday'));
assert.deepEqual(a.select(data,when,'all','children').upcoming.map(e=>e.title),['saturday']);
assert.deepEqual(a.select(data,when,'all','free').upcoming.map(e=>e.title),['free']);
assert.equal(a.select(data,when,'all','cinema').upcoming.length,1);
assert.equal(a.select(data,new Date('2026-10-26T18:00:00Z'),'all','cinema').upcoming[0].hour,'19:00');
assert.deepEqual(a.period('2026-10-25','weekend'),['2026-10-25','2026-10-25']);
assert.deepEqual(a.period('2026-10-26','weekend'),['2026-10-31','2026-11-01']);
assert.equal(a.clock(new Date('2026-10-24T22:30:00Z')).day,'2026-10-25');
assert(a.render(a.select(data,when,'today','concerts')).includes('Aucun rendez-vous'));
assert(!a.render({upcoming:[{...all.upcoming[0],title:'<img src=x onerror=alert(1)>'}],ongoing:[]}).includes('<img'));
const page=fs.readFileSync(require('node:path').join(__dirname,'../evenements-nyons/manifestations-locales/index.html'),'utf8');
const initial=page.match(/<!-- MANIFESTATIONS_RESULTS_START -->(.*?)<!-- MANIFESTATIONS_RESULTS_END -->/s)[1];
assert((initial.match(/class="sortie"/g)||[]).length<=12);
assert(!initial.includes('Chargement'));
assert.equal((page.match(/<h1\b/g)||[]).length,1);
assert(page.includes('href="https://www.vivreanyons.fr/evenements-nyons/manifestations-locales/"'));
assert.equal((page.match(/data-agenda/g)||[]).length,0,'No duplicate random agenda');
for(const block of page.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>(.*?)<\/script>/gs)) JSON.parse(block[1]);
const snapshot=JSON.parse(page.match(/<script type="application\/json" id="manifestations-data">(.*?)<\/script>/s)[1]);
if(snapshot.generatedAt) assert.equal((initial.match(/class="sortie"/g)||[]).length,a.select(snapshot,new Date(snapshot.generatedAt)).upcoming.length,'Initial HTML and client selection must agree at publication');
assert.equal(a.select(snapshot,new Date('2030-01-01T12:00:00Z')).upcoming.length,0);
console.log('PASS: Paris dates/DST, next screenings, periods, categories, no invented free access, duplicates, expired exhibitions, empty state, escaping, initial HTML parity and valid JSON-LD.');

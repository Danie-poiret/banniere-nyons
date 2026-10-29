/* Render only shared chrome before first paint. Article source is never serialized.
 * Install: npm install --prefix tools/layout (or pnpm --dir tools/layout install).
 * Run: node tools/stabilize_layout.cjs [--check] [--from-ref REF]
 * The existing browser components remain the single source of markup and styles.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const {createHash}=require('node:crypto');
const {createRequire}=require('node:module');
const requireLayout=createRequire(path.join(__dirname,'layout/package.json'));
const {parseHTML}=requireLayout('linkedom');
const {parseDocument}=requireLayout('htmlparser2');
const {selectOne,selectAll}=requireLayout('css-select');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const shared=read('assets/agenda.js'),partners=read('assets/nyons-partner-banners.js');
function between(start,end){
 const a=shared.indexOf(start),b=shared.indexOf(end,a);
 if(a<0||b<0)throw Error('Shared component boundary changed: '+start);
 return shared.slice(a,b);
}
const navigation=between('(function labelNyonsHome()', '/* Shared contact and social links');
const contact=between('(function installNyonsContact()', '  const footer=document.querySelector')+'})();';
const lodging=between('(function installNyonsLodging()', '/* Keep every existing navigation link');
const begin='<!-- nyons-layout-partners:start -->',end='<!-- nyons-layout-partners:end -->';
const styleBegin='<!-- nyons-layout-styles:start -->',styleEnd='<!-- nyons-layout-styles:end -->';
function strip(source,a,b){
 const start=source.indexOf(a);if(start<0)return source;
 const finish=source.indexOf(b,start);if(finish<0)throw Error('Unclosed layout marker');
 return source.slice(0,start)+source.slice(finish+b.length);
}
function render(original,url){
 let source=strip(strip(original,begin,end),styleBegin,styleEnd);
 // Authored homepage slots keep the same shared cards beside their subject.
 // Rebuild their contents from the component so its texts/links stay authoritative.
 source=source.replace(/(<!-- home-partner-(lezardiere|livres):start -->)[\s\S]*?(<!-- home-partner-\2:end -->)/g,'$1$3');
 const raw=parseDocument(source,{withStartIndices:true,withEndIndices:true});
 const header=selectOne('body > header',raw.children),main=selectOne('main',raw.children);
 const hero=selectOne('body > .hero,main .hero,main header',raw.children);
 // Leave standalone maps, redirects and bespoke documents alone.
 if(!header||!main||!selectOne('header .navlinks',raw.children)||!source.includes('/assets/agenda.js'))return original;
 const {document}=parseHTML(source);
 const canonical=document.querySelector('link[rel="canonical"]');
 if(!canonical||canonical.href!==url)return original;
 const context=vm.createContext({document,URL,location:new URL(url)});
 vm.runInContext(navigation+contact+lodging+partners,context,{timeout:5000});
 const cards=document.querySelector('[data-nyons-partner-cards]');
 const styles=[...document.querySelectorAll('style[data-nyons-partner-style],style[data-marseille-book-banner-style]')];
 // The accommodation's own fiche intentionally has no partner cards.
 if(cards&&!styles.length)throw Error('Partner styles missing: '+url);
 const patches=[];
 const replace=(node,text)=>patches.push({start:node.startIndex,end:node.endIndex+1,text});
 replace(header,document.querySelector('body > header').outerHTML);
 const originalLodging=selectOne('body > [data-nyons-lodging]',raw.children);
 if(!originalLodging){
  const banner=document.querySelector('body > [data-nyons-lodging]');
  if(banner)patches.push({start:header.startIndex,end:header.startIndex,text:banner.outerHTML});
 }
 // Remove obsolete banner wrappers exactly as the live component does.
 const obsolete=new Set();
 for(const node of selectAll('[data-nyons-partner-slot],iframe[src*="/banniere-livres/"],img[src*="banniere-livres-drome-ardeche.png"]',raw.children)){
  let wrapper=node;
  for(let p=node.parent;p&&p.type!=='root';p=p.parent){
   const cls=(p.attribs?.class||'').split(/\s+/);
   if((p.name==='aside'&&cls.includes('top'))||cls.includes('banner')||(p.name==='a'&&cls.includes('ad-shell'))){wrapper=p;break;}
  }
  obsolete.add(wrapper);
 }
 for(const node of obsolete)if(![...obsolete].some(p=>p!==node&&p.startIndex<node.startIndex&&p.endIndex>=node.endIndex))replace(node,'');
 const slot=selectOne('[data-nyons-partner-slot]',raw.children);
 const insertAt=hero?hero.endIndex+1:slot?slot.startIndex:obsolete.size?[...obsolete][0].startIndex:source.indexOf('>',main.startIndex)+1;
 const homeSlots=selectAll('[data-home-partner-slot]',raw.children);
 if(homeSlots.length){
  if(homeSlots.length!==2||!cards)throw Error('Incomplete homepage partner slots');
  for(const slot of homeSlots){
   const key=slot.attribs['data-home-partner-slot'];
   const card=cards.querySelector('[data-nyons-partner="'+key+'"]');
   if(!card)throw Error('Missing shared partner card: '+key);
   // The live component's existing guard also prevents reinsertion above the hero.
   card.setAttribute('data-nyons-partner-cards','');
   const at=source.indexOf('>',slot.startIndex)+1;
   patches.push({start:at,end:slot.endIndex-5,text:'<!-- home-partner-'+key+':start -->'+card.outerHTML+'<!-- home-partner-'+key+':end -->'});
  }
 }
 patches.push({start:insertAt,end:insertAt,text:begin+(!homeSlots.length&&cards?cards.outerHTML:'')+end});
 const head=selectOne('head',raw.children);
 patches.push({start:head.endIndex-6,end:head.endIndex-6,text:styleBegin+styles.map(s=>s.outerHTML).join('')+styleEnd});
 // Reverse offsets preserve every other byte, including article HTML and SEO.
 patches.sort((a,b)=>b.start-a.start||b.end-a.end);
 for(const patch of patches)source=source.slice(0,patch.start)+patch.text+source.slice(patch.end);
 return source;
}
function main(){
 const check=process.argv.includes('--check'),refIndex=process.argv.indexOf('--from-ref');
 const ref=refIndex<0?null:process.argv[refIndex+1];
 const outIndex=process.argv.indexOf('--output-dir');
 const outDir=outIndex<0?null:path.resolve(process.argv[outIndex+1]);
 if(outDir)fs.mkdirSync(outDir,{recursive:true});
 const urls=[...read('sitemap.xml').matchAll(/<loc>(https:\/\/www\.vivreanyons\.fr\/[^<]*)<\/loc>/g)].map(m=>m[1]);
 // Git's byte-preserving batch reader also supports repositories with paths that
 // differ only by case when preparing changes from a Windows checkout.
 const sources=new Map();
 if(ref){
  const paths=urls.map(url=>decodeURIComponent(new URL(url).pathname).slice(1)+'index.html');
  const bytes=execFileSync('git',['cat-file','--batch'],{cwd:root,input:paths.map(p=>ref+':'+p+'\n').join(''),maxBuffer:150e6});
  let offset=0;
  for(const p of paths){const newline=bytes.indexOf(10,offset),size=Number(bytes.subarray(offset,newline).toString().split(' ')[2]);
   if(!Number.isFinite(size))throw Error('Missing Git source: '+p);
   offset=newline+1;sources.set(p,bytes.subarray(offset,offset+size).toString('utf8'));offset+=size+1;}
 }
 const changed=[],outputs=[];let eligible=0;
 for(const url of urls){
  const route=decodeURIComponent(new URL(url).pathname);
  if(!route.endsWith('/'))continue;
  const relative=route.slice(1)+'index.html';
  const file=path.resolve(root,relative);if(!file.startsWith(root+path.sep))throw Error('Invalid path');
  const before=ref?sources.get(relative):fs.readFileSync(file,'utf8');
  const after=render(before,url);
  if(after.includes(begin))eligible++;
  if(after===before)continue;
  if(render(after,url)!==after)throw Error('Non-idempotent layout: '+relative);
  changed.push(relative);
  if(!check){
   if(outDir){const name=createHash('sha256').update(relative).digest('hex')+'.html';fs.writeFileSync(path.join(outDir,name),after);outputs.push({path:relative,file:name});}
   else fs.writeFileSync(file,after);
  }
 }
 if(outDir&&!check)fs.writeFileSync(path.join(outDir,'manifest.json'),JSON.stringify(outputs,null,2));
 console.log(JSON.stringify({eligible,changed:changed.length,files:changed}));
 if(check&&changed.length)process.exitCode=1;
}
module.exports={render};if(require.main===module)main();

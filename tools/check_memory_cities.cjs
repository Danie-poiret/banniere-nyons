const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require(process.env.MEMORY_PLAYWRIGHT || path.resolve('.memory-tools/node_modules/playwright'));
const root = path.resolve(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(root, 'tools/memory-cities.json'), 'utf8'));
const out = path.join(root, 'memory-city-evidence');
fs.mkdirSync(out, { recursive: true });
const types = { '.html':'text/html; charset=utf-8', '.css':'text/css', '.js':'text/javascript', '.webp':'image/webp', '.png':'image/png', '.jpg':'image/jpeg', '.svg':'image/svg+xml', '.json':'application/json' };
const server = http.createServer((req, res) => {
  const raw = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const file = path.resolve(root, '.'+raw+(raw.endsWith('/')?'index.html':''));
  if (!file.startsWith(root+path.sep)) { res.writeHead(403); res.end(); return; }
  try { const body=fs.readFileSync(file); res.writeHead(200, {'Content-Type':types[path.extname(file)]||'application/octet-stream'});res.end(body); }
  catch {res.writeHead(404);res.end();}
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const base='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,args:['--no-sandbox'],executablePath:process.env.MEMORY_CHROMIUM||undefined});
 const results=[];
 try {
  for(const width of [390,1365]) {
   const context=await browser.newContext({viewport:{width,height:950},reducedMotion:'reduce'});
   await context.route('**/*', route => new URL(route.request().url()).origin===base?route.continue():route.abort());
   const page=await context.newPage();
   for(const city of config.cities) {
    const response=await page.goto(base+'/'+city.path+'/',{waitUntil:'networkidle'});
    if(response.status()!==200)throw Error('City page missing: '+city.name);
    await page.locator('main img').evaluateAll(images=>images.forEach(img=>img.loading='eager'));
    await page.waitForFunction(()=>[...document.querySelectorAll('main img')].every(img=>img.complete));
    await page.locator('main img').evaluateAll(images=>Promise.all(images.map(img=>img.decode())));
    for(const image of await page.locator('main img').all()){await image.scrollIntoViewIfNeeded();await page.waitForTimeout(40);}
    await page.evaluate(()=>scrollTo(0,0));
    await page.waitForTimeout(120);
    const state=await page.evaluate(()=>({
     h1:document.querySelectorAll('h1').length,
     overflow:document.documentElement.scrollWidth>innerWidth+1,
     brokenImages:[...document.querySelectorAll('main img')].filter(img=>!img.naturalWidth).map(img=>img.getAttribute('src')),
     cards:document.querySelectorAll('main article.card').length,
     canonical:document.querySelector('link[rel="canonical"]').href,
     fontSize:parseFloat(getComputedStyle(document.querySelector('main')).fontSize)
    }));

    const routeCheck=await page.evaluate(()=>{
      const nav=document.querySelector('nav[class*="breadcrumb"]');
      const canonical=document.querySelector('link[rel="canonical"]').href;
      const visible=[...nav.querySelectorAll('a')].map(a=>({name:a.textContent.trim(),url:new URL(a.getAttribute('href'),'https://www.vivreanyons.fr/').href}));
      visible.push({name:nav.querySelector('[aria-current="page"]').textContent.trim(),url:canonical});
      const nodes=v=>Array.isArray(v)?v.flatMap(nodes):(v&&typeof v==='object'?[v,...Object.values(v).flatMap(nodes)]:[]);
      const crumbs=[...document.querySelectorAll('script[type="application/ld+json"]')].flatMap(s=>nodes(JSON.parse(s.textContent))).filter(n=>n['@type']==='BreadcrumbList');
      const schema=crumbs.length===1?crumbs[0].itemListElement.map(n=>({name:n.name,url:typeof n.item==='object'?(n.item['@id']||n.item.url):n.item})):[];
      return {visible,schema,count:crumbs.length,navFits:nav.getBoundingClientRect().right<=innerWidth+1&&nav.scrollWidth<=nav.clientWidth+1};
    });
    if(routeCheck.count!==1||!routeCheck.navFits||JSON.stringify(routeCheck.visible)!==JSON.stringify(routeCheck.schema)||routeCheck.visible[0].url!=='https://www.vivreanyons.fr/'||routeCheck.visible[1].url!=='https://www.vivreanyons.fr/memoire-de-france/')throw Error('Breadcrumb mismatch: '+JSON.stringify(routeCheck));

    if(state.h1!==1||state.overflow||state.brokenImages.length||!state.cards)throw Error(JSON.stringify({city:city.name,width,...state}));
    if(state.canonical!=='https://www.vivreanyons.fr/'+city.path+'/')throw Error('Wrong canonical');
    if(width===390){
     const toggle=page.locator('[data-mobile-menu-toggle]');
     await toggle.click();
     if(await toggle.getAttribute('aria-expanded')!=='true')throw Error('Mobile navigation did not expand');
     const menu=page.locator('details.rubriques');await menu.locator('summary').click();
     if(!await menu.getAttribute('open') && await menu.getAttribute('open')!=='' )throw Error('Mobile menu did not open');
     if(!await menu.locator('.rubriques-menu').isVisible())throw Error('Mobile menu hidden');
     await menu.locator('summary').click();
     await page.keyboard.press('Escape');
     if(await toggle.getAttribute('aria-expanded')!=='false')throw Error('Mobile navigation did not close');
    }
    if(['avignon','lyon','nyons'].includes(city.id))await page.screenshot({path:path.join(out,city.id+'-'+width+'.png'),fullPage:city.id==='avignon'});
    results.push({city:city.name,width,...state});
   }

   const examples=[
    'Hauts-de-France/Nord/Lille/bains-lillois-piscine-autrefois/',
    'Provence-Alpes-Cote-dAzur/Bouches-du-Rhone/Marseille/marche-prado-marseille-1931/',
    'Provence-Alpes-Cote-dAzur/Vaucluse/caserne-hautpoul-avignon-7e-genie/',
    'Histoire-Geo/freddy-tondeur-nyons/',
    'Provence-Alpes-Cote-dAzur/Vaucluse/Avenue-Saint-Ruf-Avignon/'
   ];
   for(const story of examples){
    await page.goto(base+'/'+story,{waitUntil:'networkidle'});

    const routeCheck=await page.evaluate(()=>{
      const nav=document.querySelector('nav[class*="breadcrumb"]');
      const canonical=document.querySelector('link[rel="canonical"]').href;
      const visible=[...nav.querySelectorAll('a')].map(a=>({name:a.textContent.trim(),url:new URL(a.getAttribute('href'),'https://www.vivreanyons.fr/').href}));
      visible.push({name:nav.querySelector('[aria-current="page"]').textContent.trim(),url:canonical});
      const nodes=v=>Array.isArray(v)?v.flatMap(nodes):(v&&typeof v==='object'?[v,...Object.values(v).flatMap(nodes)]:[]);
      const crumbs=[...document.querySelectorAll('script[type="application/ld+json"]')].flatMap(s=>nodes(JSON.parse(s.textContent))).filter(n=>n['@type']==='BreadcrumbList');
      const schema=crumbs.length===1?crumbs[0].itemListElement.map(n=>({name:n.name,url:typeof n.item==='object'?(n.item['@id']||n.item.url):n.item})):[];
      return {visible,schema,count:crumbs.length,navFits:nav.getBoundingClientRect().right<=innerWidth+1&&nav.scrollWidth<=nav.clientWidth+1};
    });
    if(routeCheck.count!==1||!routeCheck.navFits||JSON.stringify(routeCheck.visible)!==JSON.stringify(routeCheck.schema)||routeCheck.visible[0].url!=='https://www.vivreanyons.fr/'||routeCheck.visible[1].url!=='https://www.vivreanyons.fr/memoire-de-france/')throw Error('Breadcrumb mismatch: '+JSON.stringify(routeCheck));

    if(routeCheck.visible.length!==6)throw Error('Article needs six breadcrumb steps: '+story);
    if(story.includes('freddy-tondeur'))await page.screenshot({path:path.join(out,'breadcrumb-nyons-'+width+'.png'),fullPage:false});
    results.push({article:story,width,breadcrumb_steps:6,visible_schema_agreement:true,breadcrumb_fits:true});
   }

   await context.close();
  }
  fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify({network:'localhost only',pages:results},null,2));
  console.log(JSON.stringify({browser_checks:results.length,broken_images:0,horizontal_overflow:0,mobile_menu:true}));
 } finally {await browser.close();server.close();}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});

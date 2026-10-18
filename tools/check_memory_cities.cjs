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
    const state=await page.evaluate(()=>({
     h1:document.querySelectorAll('h1').length,
     overflow:document.documentElement.scrollWidth>innerWidth+1,
     brokenImages:[...document.querySelectorAll('main img')].filter(img=>!img.naturalWidth).map(img=>img.getAttribute('src')),
     cards:document.querySelectorAll('main article.card').length,
     canonical:document.querySelector('link[rel="canonical"]').href,
     fontSize:parseFloat(getComputedStyle(document.querySelector('main')).fontSize)
    }));
    if(state.h1!==1||state.overflow||state.brokenImages.length||!state.cards)throw Error(JSON.stringify({city:city.name,width,...state}));
    if(state.canonical!=='https://www.vivreanyons.fr/'+city.path+'/')throw Error('Wrong canonical');
    if(width===390){
     const menu=page.locator('details.rubriques');await menu.locator('summary').click();
     if(!await menu.getAttribute('open') && await menu.getAttribute('open')!=='' )throw Error('Mobile menu did not open');
     if(!await menu.locator('.rubriques-menu').isVisible())throw Error('Mobile menu hidden');
     await menu.locator('summary').click();
    }
    if(['avignon','lyon','nyons'].includes(city.id))await page.screenshot({path:path.join(out,city.id+'-'+width+'.png'),fullPage:city.id==='avignon'});
    results.push({city:city.name,width,...state});
   }
   await context.close();
  }
  fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify({network:'localhost only',pages:results},null,2));
  console.log(JSON.stringify({browser_checks:results.length,broken_images:0,horizontal_overflow:0,mobile_menu:true}));
 } finally {await browser.close();server.close();}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});

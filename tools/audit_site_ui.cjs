/* Responsive checks against the checkout, then Lighthouse measurements of the public pages. */
const fs=require('fs'),path=require('path'),{spawn}=require('child_process'),{pathToFileURL}=require('url');
const assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'audit-output');fs.mkdirSync(out,{recursive:true});
const {chromium}=require(path.join(root,'.audit-tools/node_modules/playwright'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function main(){
 const server=spawn('python',['-m','http.server','8765','--bind','127.0.0.1'],{cwd:root,stdio:'ignore'});
 let browser;
 try{
  for(let i=0;i<30;i++){try{await fetch('http://127.0.0.1:8765/');break;}catch{await sleep(200);}}
  browser=await chromium.launch({headless:true});const checks=[];
  for(const slug of ['', 'sante-nyons/infirmiere-domicile-nyons/', 'que-faire-nyons/les-vieux-moulins/']){
   for(const width of [320,390,1280]){
    const context=await browser.newContext({viewport:{width,height:844},deviceScaleFactor:1});const page=await context.newPage();
    await page.goto('http://127.0.0.1:8765/'+slug,{waitUntil:'networkidle',timeout:45000});
    const reject=page.locator('[data-privacy-action="reject"]');if(await reject.isVisible())await reject.click();
    const initial=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,headerHeight:document.querySelector('header').getBoundingClientRect().height,links:[...document.querySelectorAll('header a')].map(a=>a.getAttribute('href'))}));
    assert(initial.scrollWidth<=width+1,'Horizontal overflow on '+slug+' at '+width);
    const toggle=page.locator('[data-mobile-menu-toggle]');
    if(width<=800){
     assert(await toggle.isVisible(),'Mobile menu button missing');assert(initial.headerHeight<=180,'Closed mobile header too tall');
     await toggle.click();assert.equal(await toggle.getAttribute('aria-expanded'),'true');assert(await page.locator('#nyons-main-menu').isVisible());
     await page.locator('.rubriques summary').click();
     const open=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,links:[...document.querySelectorAll('header a')].map(a=>a.getAttribute('href'))}));
     assert(open.scrollWidth<=width+1,'Open menu overflows');assert.deepEqual(open.links,initial.links,'Navigation links changed');
     await page.screenshot({path:path.join(out,(slug?'article-'+slug.split('/')[1]:'home')+'-'+width+'-menu.png'),fullPage:false});
     await page.keyboard.press('Escape');assert.equal(await toggle.getAttribute('aria-expanded'),'false');assert.equal(await toggle.evaluate(e=>e===document.activeElement),true);
     await page.setViewportSize({width:1280,height:844});await toggle.waitFor({state:'hidden'});assert(!(await toggle.isVisible()));assert(await page.locator('#nyons-main-menu').isVisible());
     await page.setViewportSize({width,height:844});await toggle.waitFor({state:'visible'});assert.equal(await toggle.getAttribute('aria-expanded'),'false');
    }else{assert(!(await toggle.isVisible()));assert(await page.locator('#nyons-main-menu').isVisible());}
    await page.screenshot({path:path.join(out,(slug?'article-'+slug.split('/')[1]:'home')+'-'+width+'.png'),fullPage:false});
    checks.push({slug,width,headerHeight:initial.headerHeight,horizontalOverflow:false,allLinksPreserved:true});await context.close();
   }
  }
  const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});const page=await nojs.newPage();await page.goto('http://127.0.0.1:8765/');assert(await page.locator('.navlinks').isVisible(),'No-JavaScript navigation unavailable');await nojs.close();
  fs.writeFileSync(path.join(out,'responsive.json'),JSON.stringify(checks,null,2));console.log('RESPONSIVE_AUDIT '+JSON.stringify(checks));
 }finally{if(browser)await browser.close();server.kill();}
 // Wait for the matching public assets rather than measuring an older deployment.
 let deployed=false;
 for(let i=0;i<90;i++){
  try{const source=await(await fetch('https://www.vivreanyons.fr/assets/agenda.js',{headers:{'Cache-Control':'no-cache'}})).text();if(source.includes('installNyonsMobileNavigation')){deployed=true;break;}}catch{}
  await sleep(1000);
 }
 assert(deployed,'New public assets have not deployed; no performance score emitted');
 const lighthouse=(await import(pathToFileURL(require.resolve('lighthouse',{paths:[path.join(root,'.audit-tools')]})).href)).default;
 const {launch}=await import(pathToFileURL(require.resolve('chrome-launcher',{paths:[path.join(root,'.audit-tools')]})).href);
 const jobs=[['home','https://www.vivreanyons.fr/','mobile'],['restaurants','https://www.vivreanyons.fr/restaurants-de-nyons/','mobile'],['health','https://www.vivreanyons.fr/sante-nyons/infirmiere-domicile-nyons/','mobile'],['agenda','https://agenda.vivreanyons.fr/','mobile'],['home','https://www.vivreanyons.fr/','desktop']];
 const results=[];
 for(const [name,url,profile] of jobs){
  const chrome=await launch({chromePath:chromium.executablePath(),chromeFlags:['--headless=new','--disable-dev-shm-usage']});
  try{
   const flags={port:chrome.port,output:['json','html'],onlyCategories:['performance'],logLevel:'error'};
   if(profile==='desktop'){flags.formFactor='desktop';flags.screenEmulation={mobile:false,width:1350,height:940,deviceScaleFactor:1,disabled:false};flags.throttling={rttMs:40,throughputKbps:10240,cpuSlowdownMultiplier:1};}
   const result=await lighthouse(url,flags);assert(!result.lhr.runtimeError,JSON.stringify(result.lhr.runtimeError));
   const stem=name+'-'+profile;fs.writeFileSync(path.join(out,stem+'.json'),result.report[0]);fs.writeFileSync(path.join(out,stem+'.html'),result.report[1]);
   const l=result.lhr,a=l.audits;const record={name,url,profile,fetchTime:l.fetchTime,lighthouseVersion:l.lighthouseVersion,score:Math.round(l.categories.performance.score*100),LCPms:a['largest-contentful-paint'].numericValue,CLS:a['cumulative-layout-shift'].numericValue,TBTms:a['total-blocking-time'].numericValue,warnings:l.runWarnings};
   results.push(record);console.log('LIGHTHOUSE_RESULT '+JSON.stringify(record));
  }finally{await chrome.kill();}
 }
 fs.writeFileSync(path.join(out,'performance-summary.json'),JSON.stringify({method:'Lighthouse laboratory; mobile simulated throttling, desktop documented settings; one run per page/profile; no CrUX or field INP measurement',results},null,2));
 console.log('SITE_UI_AUDIT_COMPLETE');
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1;});

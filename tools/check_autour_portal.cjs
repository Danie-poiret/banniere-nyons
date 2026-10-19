/* Branch-only measurements of this page; no deployment or production writes. */
const fs=require('fs'),path=require('path'),{spawn}=require('child_process'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const root=path.resolve(__dirname,'..'),out=path.join(root,'audit-output/autour'),deps=path.join(root,'.audit-tools');fs.mkdirSync(out,{recursive:true});
const {chromium}=require(path.join(deps,'node_modules/playwright'));
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function main(){
 const server=spawn('python',['-m','http.server','8766','--bind','127.0.0.1'],{cwd:root,stdio:'ignore'});let browser;
 try{
  for(let i=0;i<40;i++){try{await fetch('http://127.0.0.1:8766/');break;}catch{await wait(200);}}
  const url='http://127.0.0.1:8766/a-faire-autour-de-Nyons/';browser=await chromium.launch({headless:true});
  for(const width of [320,390,1280]){
   const context=await browser.newContext({viewport:{width,height:900}});const page=await context.newPage();const failures=[];
   page.on('pageerror',e=>failures.push(e.message));page.on('response',r=>{if(r.url().startsWith('http://127.0.0.1:8766/')&&r.status()>=400)failures.push(r.url()+': '+r.status());});
   await page.goto(url,{waitUntil:'networkidle'});
   const reject=page.locator('[data-privacy-action="reject"]');if(await reject.isVisible())await reject.click();
   assert((await page.evaluate(()=>document.documentElement.scrollWidth))<=width,'Overflow '+width);
   assert.equal(await page.locator('[data-autour-card]').count(),49);assert.equal(await page.locator('#autour-category option').count(),7);
   const hero=await page.locator('.ap-hero-visual').boundingBox(),heading=await page.locator('h1').boundingBox();assert(heading.y>=hero.y&&heading.y+heading.height<=hero.y+hero.height,'Hero title clipped');
   await page.screenshot({path:path.join(out,'page-'+width+'.png')});
   await page.locator('#autour-search').fill('piegon');assert.equal(await page.locator('[data-autour-card]:visible').count(),1,'Accent insensitive search');
   await page.getByRole('button',{name:'Tout afficher',exact:true}).click();assert.equal(await page.locator('[data-autour-card]:visible').count(),49);
   await page.locator('#autour-category').selectOption('villages');assert((await page.locator('[data-autour-card]:visible').count())>0);
   assert(await page.locator('[data-autour-card]:visible').evaluateAll(cards=>cards.every(e=>e.dataset.group==='villages')));
   await page.locator('#autour-season').selectOption('hiver');assert(await page.locator('[data-autour-card]:visible').evaluateAll(cards=>cards.every(e=>e.dataset.seasons.includes('hiver'))));
   await page.locator('#autour-search').fill('zzzzzz');assert(await page.locator('#autour-empty').isVisible());
   await page.getByRole('button',{name:'Tout afficher',exact:true}).click();assert.equal(await page.locator('[data-autour-card]:visible').count(),49);
   await page.locator('.ap-faq summary').first().focus();await page.keyboard.press('Enter');assert.equal(await page.locator('.ap-faq details').first().getAttribute('open'),'');
   assert.deepEqual(failures,[],'Browser errors');await context.close();
  }
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}}),page=await context.newPage();await page.goto(url);
  assert.equal(await page.locator('[data-autour-card]:visible').count(),49);assert(!(await page.locator('#autour-filters').isVisible()));await context.close();await browser.close();browser=null;
  fs.writeFileSync(path.join(out,'functional.json'),JSON.stringify({widths:[320,390,1280],guidesWithoutJS:49,search:true,categories:true,seasons:true,emptyState:true,reset:true,keyboardFAQ:true},null,2));
  const lighthouse=(await import(pathToFileURL(require.resolve('lighthouse',{paths:[deps]})).href)).default;
  const {launch}=await import(pathToFileURL(require.resolve('chrome-launcher',{paths:[deps]})).href);const results=[];
  for(const profile of ['mobile','desktop'])for(const version of ['before','after']){
   const chrome=await launch({chromePath:chromium.executablePath(),chromeFlags:['--headless=new','--disable-dev-shm-usage','--no-sandbox']});
   try{
    const flags={port:chrome.port,output:['json','html'],onlyCategories:['performance','accessibility','seo'],logLevel:'error'};
    if(profile==='desktop'){flags.formFactor='desktop';flags.screenEmulation={mobile:false,width:1350,height:940,deviceScaleFactor:1,disabled:false};flags.throttling={rttMs:40,throughputKbps:10240,cpuSlowdownMultiplier:1};}
    const result=await lighthouse(version==='before'?'http://127.0.0.1:8766/.audit-tools/before/':url,flags);assert(!result.lhr.runtimeError,JSON.stringify(result.lhr.runtimeError));
    const stem=version+'-'+profile;fs.writeFileSync(path.join(out,stem+'.json'),result.report[0]);fs.writeFileSync(path.join(out,stem+'.html'),result.report[1]);
    const l=result.lhr,a=l.audits,record={version,profile,fetchTime:l.fetchTime,lighthouseVersion:l.lighthouseVersion,score:Math.round(l.categories.performance.score*100),accessibility:Math.round(l.categories.accessibility.score*100),seo:Math.round(l.categories.seo.score*100),LCPms:a['largest-contentful-paint'].numericValue,CLS:a['cumulative-layout-shift'].numericValue,TBTms:a['total-blocking-time'].numericValue,warnings:l.runWarnings};results.push(record);console.log('PERFORMANCE '+JSON.stringify(record));
   }finally{await chrome.kill();}
  }
  fs.writeFileSync(path.join(out,'performance-summary.json'),JSON.stringify({method:'One laboratory run per profile/version on the same Linux worker and HTTP server; mobile simulated throttling. Not field CrUX or INP. Existing shared scripts retained.',results},null,2));
 }finally{if(browser)await browser.close();server.kill();}
}
main().catch(e=>{console.error(e.stack||e);process.exitCode=1;});


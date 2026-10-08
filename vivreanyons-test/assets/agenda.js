/* Home link label shared by every page. */
(function labelNyonsHome(){
  document.querySelectorAll('header .navlinks a').forEach(link=>{
    if(link.textContent.trim()==='Accueil') link.textContent='Nyons accueil';
  });
})();
/* Direct links shared by the site navigation. */
(function installNyonsMenuShortcuts(){
  const menu=document.querySelector('header .navlinks');
  if(!menu) return;
  const sections=menu.querySelector('.rubriques');
  [
    {key:'hebergement',label:'Où dormir à Nyons ?',url:'https://www.vivreanyons.fr/ou-dormir-a-nyons/'},
    {key:'brocantes',label:'Brocantes',url:'https://www.vivreanyons.fr/evenements-nyons/Brocantes--Vides-greniers-Nyons/'},
    {key:'cinema',label:'Programme cinéma',url:'https://www.vivreanyons.fr/infos-pratiques-nyons/cinema-nyons/'},
    {key:'pharmacie-garde',label:'Pharmacie de garde',url:'https://www.vivreanyons.fr/infos-pratiques-nyons/pharmacie-de-garde-nyons/'}
  ].forEach(item=>{
    let link=[...menu.children].find(child=>child.tagName==='A'&&(child.getAttribute('data-nyons-shortcut')===item.key||child.href===item.url));
    if(!link) link=document.createElement('a');
    link.setAttribute('data-nyons-shortcut',item.key);
    link.href=item.url;
    link.textContent=item.label;
    menu.insertBefore(link,sections);
  });
})();
/* Shared contact and social links requested by the site owner. */
(function installNyonsContact(){
  const nav=document.querySelector('.nav'),brand=nav&&nav.querySelector('.brand');
  if(brand&&!nav.querySelector('[data-nyons-follow]')){
    const group=document.createElement('div');
    group.className='nav-brand-group';brand.before(group);group.append(brand);
    const follow=document.createElement('a');
    follow.className='facebook-follow';follow.setAttribute('data-nyons-follow','');
    follow.href='https://www.facebook.com/groups/nyonsaujourdhui';
    follow.target='_blank';follow.rel='noopener noreferrer';
    follow.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="12" fill="#1877f2"/><path fill="#fff" d="M13.6 20v-7.3h2.5l.4-2.8h-2.9V8.1c0-.8.2-1.4 1.5-1.4h1.5V4.2c-.3 0-1.2-.2-2.2-.2-2.2 0-3.7 1.3-3.7 3.8v2.1H8.2v2.8h2.5V20z"/></svg><span>Me suivre sur Facebook</span>';
    group.append(follow);
  }
  const footer=document.querySelector('footer.footer');
  if(footer){
    const comparison=footer.querySelector('a[href*="vivreanyons.fr"]');
    const homeLinks=footer.querySelector('[data-home-footer-links]');
    const content=document.createElement('div');content.className='wrap site-footer-content';
    content.innerHTML='<p><strong>Me contacter <a href="mailto:contact@vivreanyons.fr">contact@vivreanyons.fr</a></strong></p><p><strong>© 2025 VivreAnyons.fr | Votre guide de la vie à Nyons, entre oliveraies centenaires, <a href="https://www.vivreanyons.fr/a-faire-autour-de-Nyons/marches-provencaux">marché provençal</a> et patrimoine authentique.</strong></p><p><strong>Suivez-nous : <a href="https://www.facebook.com/groups/nyonsaujourdhui" target="_blank" rel="noopener noreferrer">Facebook Nyons</a> - <a href="https://www.facebook.com/tresorsdenyons" target="_blank" rel="noopener noreferrer">Nyons</a> - <a href="https://agenda.vivreanyons.fr/semaines/">agenda nyons</a> - <a href="https://agenda.vivreanyons.fr/">Que faire à Nyons</a> - <a href="https://agenda.vivreanyons.fr/cinema/">Cinéma</a> - <a href="https://drome.vivreanyons.fr/evenements/">Agenda Drôme</a></strong></p>';
    if(comparison){const p=document.createElement('p');p.className='footer-comparison';p.append(comparison);content.append(p);}
    if(homeLinks) content.append(homeLinks);
    footer.replaceChildren(content);
  }
})();
/* Banner supplied by the site owner; shown below the green page heading. */
(function installNyonsBanner(){
  const hero=document.querySelector('body > .hero');
  if(!hero || document.querySelector('[data-nyons-banner]')) return;
  const banner=document.createElement('aside');
  banner.className='site-banner';
  banner.setAttribute('data-nyons-banner','');
  banner.setAttribute('aria-label','Sélection de vieux livres sur Nyons');
  banner.style.cssText='width:min(1120px,92%);margin:24px auto 0';
  const link=document.createElement('a');
  link.href='https://amzn.to/3VzucHH';
  link.target='_blank';
  link.rel='sponsored noopener noreferrer';
  link.title='Voir ma sélection de livres anciens sur Nyons';
  const image=document.createElement('img');
  image.src='/banniere-nyons/vivreanyons-test/assets/nyons-livres-banner.webp';
  image.alt='Vieux livres sur Nyons que je recommande : histoire, souvenirs et cartes postales anciennes. Voir ma sélection sur Amazon.';
  image.width=2172;
  image.height=724;
  image.loading='lazy';
  image.decoding='async';
  image.style.cssText='display:block;width:100%;height:auto';
  link.append(image);
  banner.append(link);
  hero.insertAdjacentElement('afterend',banner);
})();
const AGENDA_DATA='https://raw.githubusercontent.com/Danie-poiret/agenda-nyons/main/agenda.json';
function slugify(s){return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/['’]/g,'-').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').replace(/-+/g,'-')}
function fmtDate(s){if(!s)return'';const [y,m,d]=s.split('-').map(Number);return new Intl.DateTimeFormat('fr-FR',{day:'numeric',month:'long'}).format(new Date(y,m-1,d))}
function agendaToday(now=new Date()){
  const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
  const part=type=>parts.find(p=>p.type===type).value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}
function agendaSixMonthsAfter(today){
  const [year,month,day]=today.split('-').map(Number);
  const lastDay=new Date(Date.UTC(year,month-1+7,0)).getUTCDate();
  return new Date(Date.UTC(year,month-1+6,Math.min(day,lastDay))).toISOString().slice(0,10);
}
function selectAgendaEvents(items,now=new Date(),random=Math.random){
  const today=agendaToday(now),until=agendaSixMonthsAfter(today),seen=new Set();
  const upcoming=(items||[]).filter(event=>{
    if(!event||!event.title||!/^\d{4}-\d{2}-\d{2}$/.test(event.start_date||''))return false;
    const key=event.start_date+'|'+slugify(event.title);
    if(seen.has(key)||(event.end_date||event.start_date)<today)return false;
    seen.add(key);return true;
  }).sort((a,b)=>a.start_date.localeCompare(b.start_date));
  const first=upcoming.slice(0,3);
  const pool=upcoming.slice(3).filter(event=>event.start_date>=today&&event.start_date<=until);
  for(let i=pool.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[pool[i],pool[j]]=[pool[j],pool[i]];}
  return first.concat(pool.slice(0,3));
}
function agendaEscape(value){return String(value||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function agendaSummary(summary){
  const text=String(summary||'Retrouvez les informations pratiques sur la fiche événement.').split('Abonnement aux informations de la ville de Nyons')[0].replace(/\s+1 2 3 4 5.*$/,'').trim();
  return text.length>240?text.slice(0,237).trimEnd()+'…':text;
}
function agendaEventSlug(event){
  const title=String(event.title||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^\x00-\x7F]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,82).replace(/-+$/g,'')||'evenement';
  return title+'-'+event.start_date;
}
function agendaEventUrl(event,published){
  const local='https://agenda.vivreanyons.fr/evenements/'+agendaEventSlug(event)+'/';
  if(published&&published.has(local))return local;
  return 'https://agenda.vivreanyons.fr/';
}
async function agendaPublishedUrls(){
  try{
    const response=await fetch('https://raw.githubusercontent.com/Danie-poiret/agenda-nyons/main/sitemap.xml',{cache:'no-store'});
    if(!response.ok)return null;
    const xml=new DOMParser().parseFromString(await response.text(),'application/xml');
    return new Set([...xml.getElementsByTagName('loc')].map(el=>el.textContent.trim()).filter(url=>url.startsWith('https://agenda.vivreanyons.fr/evenements/')));
  }catch(error){return null;}
}
const DROME_DATA='https://raw.githubusercontent.com/Danie-poiret/drome-provencale/main/agenda.json';
const DROME_INDEX='https://raw.githubusercontent.com/Danie-poiret/drome-provencale/main/evenements/index.html';
function agendaDailyRandom(seed){
  let value=2166136261;
  for(const char of seed){value^=char.charCodeAt(0);value=Math.imul(value,16777619);}
  return ()=>{value+=0x6D2B79F5;let t=value;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};
}
function agendaDromeKey(title,commune){return slugify(title)+'|'+slugify(commune);}
async function loadDromeEvents(){
  const responses=await Promise.all([fetch(DROME_DATA,{cache:'no-store'}),fetch(DROME_INDEX,{cache:'no-store'})]);
  if(responses.some(response=>!response.ok))throw new Error('agenda Drôme');
  const [data,source]=await Promise.all([responses[0].json(),responses[1].text()]);
  const page=new DOMParser().parseFromString(source,'text/html'),published=new Map();
  page.querySelectorAll('.village-section').forEach(section=>{
    const commune=section.getAttribute('data-village');
    section.querySelectorAll('a.card[href]').forEach(card=>{
      const title=card.querySelector('strong')?.textContent.trim();
      const url=card.getAttribute('href');
      if(!title||!/^https:\/\/drome\.vivreanyons\.fr\/evenements\/[^/?#]+\/$/.test(url||''))return;
      const key=agendaDromeKey(title,commune);
      if(!published.has(key))published.set(key,[]);
      published.get(key).push(url);
    });
  });
  return (data.events||[]).map(event=>{
    const urls=published.get(agendaDromeKey(event.title,event.commune))||[];
    const url=urls.find(url=>url.includes('-'+event.start_date+'/')||url.includes('-'+event.start_date+'-'));
    return {...event,published_url:url};
  }).filter(event=>event.published_url);
}
function selectDromeEvents(items,now=new Date(),page=location.pathname){
  const today=agendaToday(now),until=agendaSixMonthsAfter(today),seen=new Set();
  const pool=(items||[]).filter(event=>{
    if(!event?.published_url||!event.title||!/^\d{4}-\d{2}-\d{2}$/.test(event.start_date||''))return false;
    if((event.end_date||event.start_date)<today||event.start_date>until||seen.has(event.published_url))return false;
    seen.add(event.published_url);return true;
  });
  const distance=event=>typeof event.distance_from_nyons_km==='number'&&Number.isFinite(event.distance_from_nyons_km)&&event.distance_from_nyons_km>=0?event.distance_from_nyons_km:Infinity;
  const near=pool.filter(event=>distance(event)<=30);
  // Nearby outings form the daily pool; expand only when there are fewer than three.
  const candidates=near.length>=3?near:near.concat(pool.filter(event=>distance(event)>30).sort((a,b)=>distance(a)-distance(b)).slice(0,3-near.length));
  const random=agendaDailyRandom('drome|'+page);
  candidates.sort((a,b)=>a.published_url.localeCompare(b.published_url));
  for(let i=candidates.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[candidates[i],candidates[j]]=[candidates[j],candidates[i]];}
  if(!candidates.length)return [];
  const day=Math.floor(Date.parse(today+'T00:00:00Z')/86400000);
  // Rotation guarantees a different trio on consecutive days when the pool has >3 outings.
  const start=(day*3)%candidates.length;
  return Array.from({length:Math.min(3,candidates.length)},(_,index)=>candidates[(start+index)%candidates.length]);
}
function renderAgendaEvent(event,url,drome=false){
  const summary=drome?event.description:event.summary;
  const place=drome?`<p class="event-place">📍 ${agendaEscape(event.commune)}</p>`:'';
  return `<article class="event${drome?' event-drome':''}"><div class="event-date">${fmtDate(event.start_date)}${event.end_date&&event.end_date!==event.start_date?' → '+fmtDate(event.end_date):''}</div><h3><a href="${agendaEscape(url)}">${agendaEscape(event.title)}</a></h3>${place}<p>${agendaEscape(agendaSummary(summary))}</p></article>`;
}
async function loadAgenda(){
  const roots=[...document.querySelectorAll('[data-agenda]')];if(!roots.length)return;
  const [nyons,drome]=await Promise.allSettled([
    Promise.all([fetch(AGENDA_DATA,{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('agenda');return response.json();}),agendaPublishedUrls()]),
    loadDromeEvents()
  ]);
  roots.forEach(root=>{
    let content='';
    if(nyons.status==='fulfilled'){
      const [data,published]=nyons.value;
      const events=selectAgendaEvents(data.events);
      content=events.map(event=>renderAgendaEvent(event,agendaEventUrl(event,published))).join('')||'<p>Aucun événement à venir pour le moment.</p>';
    }else content='<p>Les prochains événements sont disponibles sur <a href="https://agenda.vivreanyons.fr/">agenda.vivreanyons.fr</a>.</p>';
    content+='<h3 class="agenda-drome-heading">À découvrir près de Nyons <a href="https://drome.vivreanyons.fr/evenements/">Agenda Drôme →</a></h3>';
    if(drome.status==='fulfilled'){
      const events=selectDromeEvents(drome.value);
      content+=events.map(event=>renderAgendaEvent(event,event.published_url,true)).join('')||'<p>Retrouvez les prochaines sorties dans l’<a href="https://drome.vivreanyons.fr/evenements/">agenda Drôme</a>.</p>';
    }else content+='<p>Retrouvez les sorties dans l’<a href="https://drome.vivreanyons.fr/evenements/">agenda Drôme</a>.</p>';
    root.innerHTML=content;
  });
}
let agendaRenderedDay=agendaToday();
function refreshDailyAgenda(){
  const today=agendaToday();
  if(today!==agendaRenderedDay){agendaRenderedDay=today;loadAgenda();}
}
// Refresh even if a visitor keeps the page open across the date change in France.
setInterval(refreshDailyAgenda,60000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshDailyAgenda();});

function simplifyPontRomanPhotos(){
  if(!location.pathname.includes('/Pont-Roman-de-Nyons'))return;
  document.querySelectorAll('main .photo-stack').forEach(stack=>{if(!stack.querySelector('figure'))stack.remove()});
  [...document.querySelectorAll('main p')].forEach(p=>{if(p.textContent.includes('Image improbable : une autruche'))p.remove()});
}
document.addEventListener('DOMContentLoaded',()=>{simplifyPontRomanPhotos();loadAgenda()});
/* Navigation by article section on every detailed page. */
(function installArticleContents(){
  const article=document.querySelector('main article.feature-story, main .content > article:not(.card)');
  if(!article || article.querySelector('[data-article-contents]')) return;
  const headings=[...article.querySelectorAll('h2,h3')];
  const layout=article.parentElement;
  const faq=layout.querySelector(':scope > .faq h2');
  if(faq) headings.push(faq);
  const entries=headings.filter(h=>h.textContent.trim());
  if(!entries.length)return;
  entries.forEach((h,index)=>{
    if(!h.id){const stem=h.textContent.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,80)||'paragraphe';let id='section-'+stem,n=2;while(document.getElementById(id))id='section-'+stem+'-'+n++;h.id=id;}
    h.classList.add('article-section-anchor');
  });
  function contents(inline){
    const nav=document.createElement('nav');nav.className='article-contents side-card'+(inline?' toc-inline':' toc-sidebar');nav.setAttribute('aria-label','Sommaire de la fiche');nav.setAttribute('data-article-contents','');
    const title=document.createElement('p');title.className='contents-title';title.textContent='Dans cette fiche';nav.append(title);
    const list=document.createElement('ul');list.className='contents-links';
    entries.forEach(h=>{const item=document.createElement('li');if(h.tagName==='H3')item.className='contents-subsection';const a=document.createElement('a');a.href='#'+encodeURIComponent(h.id);a.textContent=h.textContent.trim();item.append(a);list.append(item);});
    nav.append(list);return nav;
  }
  const sidebar=layout.querySelector(':scope > .right-sidebar');
  const inline=contents(true);article.prepend(inline);
  if(sidebar){inline.classList.add('has-desktop-contents');sidebar.prepend(contents(false));}
})();

/* Optional embedded services remain blocked until the visitor chooses them. */
(function installPrivacyChoices(){
  if(!document.body || document.querySelector('[data-privacy-panel]'))return;
  const KEY='vivreanyons:privacy:v1',VERSION=1;
  const script=document.currentScript;
  const policyUrl=script?new URL('../cookies/',script.src).href:'/cookies/';
  const frames=[...document.querySelectorAll('iframe[data-privacy-category][data-src]')];
  let choice=null,lastFocus=null;
  try{
    const saved=JSON.parse(localStorage.getItem(KEY));
    if(saved&&saved.version===VERSION&&typeof saved.videos==='boolean'&&typeof saved.maps==='boolean'&&Number.isFinite(saved.expires)&&saved.expires>Date.now())choice=saved;
  }catch(error){}
  // One GA4 destination: the GT alias shown in Google is not configured twice.
  const ANALYTICS_ID='G-X0T2SGWSWX';
  const analyticsState={started:false,loaded:false,enabled:false,script:null};
  const analyticsSite=/^(www\.)?vivreanyons\.fr$/.test(location.hostname)&&!/^\/(?:banniere-nyons\/)?vivreanyons-test(?:\/|$)/.test(location.pathname);
  const deniedConsent={analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'};
  function clearAnalyticsCookies(){
    const names=['_ga','_ga_'+ANALYTICS_ID.slice(2).replace(/-/g,'_')];
    const domains=['',location.hostname,'.'+location.hostname,'vivreanyons.fr','.vivreanyons.fr'];
    names.forEach(name=>domains.forEach(domain=>{
      document.cookie=name+'=; Max-Age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'+(domain?'; domain='+domain:'')+'; SameSite=Lax; Secure';
    }));
  }
  function applyAnalytics(){
    const allowed=analyticsSite&&!!(choice&&choice.analytics===true&&choice.expires>Date.now());
    window['ga-disable-'+ANALYTICS_ID]=!allowed;
    if(!allowed){
      if(analyticsState.enabled&&typeof window.gtag==='function')window.gtag('consent','update',deniedConsent);
      analyticsState.enabled=false;
      if(analyticsState.script&&!analyticsState.loaded){analyticsState.script.remove();analyticsState.script=null;}
      if(analyticsSite)clearAnalyticsCookies();
      return;
    }
    if(analyticsState.enabled&&analyticsState.script)return;
    window.dataLayer=window.dataLayer||[];
    if(typeof window.gtag!=='function')window.gtag=function(){window.dataLayer.push(arguments);};
    if(!analyticsState.started){
      window.gtag('consent','default',deniedConsent);
      window.gtag('consent','update',{...deniedConsent,analytics_storage:'granted'});
      window.gtag('js',new Date());
      let referrer='';
      try{if(document.referrer)referrer=new URL(document.referrer).origin;}catch(error){}
      window.gtag('config',ANALYTICS_ID,{
        allow_google_signals:false,
        allow_ad_personalization_signals:false,
        cookie_domain:location.hostname,
        cookie_path:'/',
        cookie_expires:15552000,
        cookie_update:false,
        page_location:location.origin+location.pathname,
        page_referrer:referrer
      });
      analyticsState.started=true;
    }else if(!analyticsState.enabled)window.gtag('consent','update',{...deniedConsent,analytics_storage:'granted'});
    analyticsState.enabled=true;
    if(!analyticsState.loaded&&!analyticsState.script){
      const tag=document.createElement('script');tag.async=true;
      tag.dataset.nyonsAnalytics=ANALYTICS_ID;
      tag.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(ANALYTICS_ID);
      tag.addEventListener('load',()=>{analyticsState.loaded=true;});
      tag.addEventListener('error',()=>{tag.remove();analyticsState.script=null;});
      analyticsState.script=tag;document.head.append(tag);
    }
  }
  const panel=document.createElement('section');panel.className='privacy-panel';panel.dataset.privacyPanel='';
  panel.setAttribute('role','dialog');panel.setAttribute('aria-labelledby','privacy-title');
  panel.innerHTML='<h2 id="privacy-title">Votre choix pour les cookies</h2><p>Le site reste accessible sans les services externes. Les vidéos YouTube, les vidéos Facebook et les cartes peuvent transmettre des informations de connexion à leurs fournisseurs et utiliser des cookies ou autres traceurs. La mesure d’audience Google Analytics est également facultative et démarre seulement si vous l’autorisez.</p><p class="privacy-information"><a href="'+policyUrl+'">En savoir plus sur les cookies</a></p><div class="privacy-actions"><button type="button" data-privacy-action="accept">Accepter</button><button type="button" data-privacy-action="reject">Refuser</button><button type="button" data-privacy-action="configure" aria-expanded="false" aria-controls="privacy-options">Paramétrer</button></div><form id="privacy-options" class="privacy-options" hidden><label><input type="checkbox" name="videos"> <span><strong>Vidéos YouTube</strong><br>Autoriser le lecteur vidéo de Google / YouTube et ses traceurs éventuels.</span></label><label><input type="checkbox" name="facebook"> <span><strong>Vidéos Facebook</strong><br>Autoriser le lecteur de Meta / Facebook et ses traceurs éventuels.</span></label><label><input type="checkbox" name="maps"> <span><strong>Cartes interactives</strong><br>Autoriser Google Maps et la carte des sports avec ses fonds OpenStreetMap et ressources externes.</span></label><label><input type="checkbox" name="analytics"> <span><strong>Mesure d’audience</strong><br>Autoriser Google Analytics pour mesurer les visites du site. Les options publicitaires restent désactivées.</span></label><p>Le stockage de votre choix est nécessaire pour le mémoriser pendant six mois. Il reste dans votre navigateur.</p><div class="privacy-actions"><button type="submit">Enregistrer mes choix</button><button type="button" data-privacy-action="cancel">Annuler</button></div></form>';
  document.body.append(panel);
  const options=panel.querySelector('form'),videos=options.elements.videos,maps=options.elements.maps,facebook=options.elements.facebook,analytics=options.elements.analytics;
  const configure=panel.querySelector('[data-privacy-action="configure"]');
  function apply(){
    videos.checked=!!(choice&&choice.videos);maps.checked=!!(choice&&choice.maps);facebook.checked=!!(choice&&choice.facebook);analytics.checked=!!(choice&&choice.analytics);
    applyAnalytics();
    frames.forEach(frame=>{
      const allowed=!!(choice&&choice[frame.dataset.privacyCategory]);
      const placeholder=frame.previousElementSibling;
      frame.hidden=!allowed;
      if(placeholder&&placeholder.matches('[data-privacy-placeholder]'))placeholder.hidden=allowed;
      if(allowed){if(frame.getAttribute('src')!==frame.dataset.src)frame.setAttribute('src',frame.dataset.src);}
      else if(frame.hasAttribute('src'))frame.removeAttribute('src');
    });
  }
  function setChoice(allowVideos,allowMaps,allowFacebook=false,allowAnalytics=false){
    const expiry=new Date();expiry.setMonth(expiry.getMonth()+6);
    choice={version:VERSION,videos:allowVideos,maps:allowMaps,facebook:allowFacebook,analytics:allowAnalytics,expires:expiry.getTime()};
    try{localStorage.setItem(KEY,JSON.stringify(choice));}catch(error){}
    apply();panel.hidden=true;options.hidden=true;configure.setAttribute('aria-expanded','false');
    if(lastFocus&&lastFocus.isConnected)lastFocus.focus();
  }
  function show(settings=false,category=null){
    lastFocus=document.activeElement;panel.hidden=false;
    videos.checked=!!(choice&&choice.videos);maps.checked=!!(choice&&choice.maps);facebook.checked=!!(choice&&choice.facebook);analytics.checked=!!(choice&&choice.analytics);
    options.hidden=!settings;configure.setAttribute('aria-expanded',String(settings));
    const focus=category==='videos'?videos:category==='maps'?maps:category==='facebook'?facebook:category==='analytics'?analytics:settings?videos:panel.querySelector('button');
    focus.focus({preventScroll:true});
  }
  panel.querySelector('[data-privacy-action="accept"]').addEventListener('click',()=>setChoice(true,true,true,true));
  panel.querySelector('[data-privacy-action="reject"]').addEventListener('click',()=>setChoice(false,false));
  configure.addEventListener('click',()=>{options.hidden=!options.hidden;configure.setAttribute('aria-expanded',String(!options.hidden));if(!options.hidden)videos.focus();});
  options.addEventListener('submit',event=>{event.preventDefault();setChoice(videos.checked,maps.checked,facebook.checked,analytics.checked);});
  panel.querySelector('[data-privacy-action="cancel"]').addEventListener('click',()=>{if(choice){panel.hidden=true;lastFocus?.focus();}else{options.hidden=true;configure.setAttribute('aria-expanded','false');}});
  panel.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();if(choice){panel.hidden=true;lastFocus?.focus();}else setChoice(false,false);}});
  document.querySelectorAll('[data-privacy-placeholder] button').forEach(button=>button.addEventListener('click',()=>show(true,button.closest('[data-privacy-placeholder]').dataset.privacyPlaceholder)));
  document.querySelectorAll('[data-open-privacy]').forEach(button=>button.addEventListener('click',()=>show(true)));
  const footer=document.querySelector('footer .wrap');
  if(footer){
    const p=document.createElement('p');p.className='privacy-footer';
    const button=document.createElement('button');button.type='button';button.className='privacy-manage';button.textContent='Gérer mes cookies';button.addEventListener('click',()=>show(true));
    const link=document.createElement('a');link.href=policyUrl;link.textContent='Cookies et confidentialité';
    p.append(button,document.createTextNode(' · '),link);footer.append(p);
  }
  window.addEventListener('storage',event=>{
    if(event.key!==KEY&&event.key!==null)return;
    try{const saved=JSON.parse(event.newValue);choice=saved&&saved.version===VERSION&&typeof saved.videos==='boolean'&&typeof saved.maps==='boolean'&&Number.isFinite(saved.expires)&&saved.expires>Date.now()?saved:null;}catch(error){choice=null;}
    apply();panel.hidden=!!(choice&&typeof choice.analytics==='boolean');
  });
  apply();panel.hidden=!!(choice&&typeof choice.analytics==='boolean');
  setInterval(()=>{if(choice&&choice.expires<=Date.now()){choice=null;apply();panel.hidden=false;}},60000);
})();

/* Visitor-visible lodging message; excluded from search-result snippets. */
(function installNyonsLodging(){
  if(!document.body || document.querySelector('[data-nyons-lodging]')) return;
  const banner=document.createElement('div');
  banner.className='lodging-banner';
  banner.setAttribute('data-nyons-lodging','');
  banner.setAttribute('data-nosnippet','');
  banner.setAttribute('role','region');
  banner.setAttribute('aria-label','Le logement de Papy Chris à Nyons');
  banner.innerHTML='<div class="lodging-banner-inner"><p><strong>🔥 STOP AUX MAUVAISES LOCATIONS À NYONS</strong><span>👉 Papy Chris t’a trouvé ton logement 👍</span></p><div class="lodging-banner-actions"><a class="lodging-see" href="https://www.lalezardierenyons.com/situation-contact" target="_blank" rel="sponsored noopener noreferrer">Voir ↗</a><a class="lodging-whatsapp" href="https://wa.me/33632076124" target="_blank" rel="noopener noreferrer"><span aria-hidden="true">📞</span> WhatsApp · 06 32 07 61 24</a></div></div>';
  document.body.prepend(banner);
})();

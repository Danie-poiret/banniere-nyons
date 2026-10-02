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
    const content=document.createElement('div');content.className='wrap site-footer-content';
    content.innerHTML='<p><strong>Me contacter <a href="mailto:contact@vivreanyons.fr">contact@vivreanyons.fr</a></strong></p><p><strong>© 2025 VivreAnyons.fr | Votre guide de la vie à Nyons, entre oliveraies centenaires, <a href="https://www.vivreanyons.fr/a-faire-autour-de-Nyons/marches-provencaux">marché provençal</a> et patrimoine authentique.</strong></p><p><strong>Suivez-nous : <a href="https://www.facebook.com/groups/nyonsaujourdhui" target="_blank" rel="noopener noreferrer">Facebook Nyons</a> - <a href="https://www.facebook.com/tresorsdenyons" target="_blank" rel="noopener noreferrer">Nyons</a> - <a href="https://agenda.vivreanyons.fr/semaines/">agenda nyons</a> - <a href="https://agenda.vivreanyons.fr/">Que faire à Nyons</a> - <a href="https://drome.vivreanyons.fr/evenements/">Agenda Drôme</a></strong></p>';
    if(comparison){const p=document.createElement('p');p.className='footer-comparison';p.append(comparison);content.append(p);}
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
async function loadAgenda(){
  const roots=[...document.querySelectorAll('[data-agenda]')];if(!roots.length)return;
  try{
    const [response,published]=await Promise.all([fetch(AGENDA_DATA,{cache:'no-store'}),agendaPublishedUrls()]);if(!response.ok)throw new Error('agenda');
    const data=await response.json();
    roots.forEach(root=>{
      const events=selectAgendaEvents(data.events);
      if(!events.length){root.innerHTML='<p>Aucun événement à venir pour le moment.</p>';return;}
      root.innerHTML=events.map(event=>{
        const url=agendaEventUrl(event,published);
        return `<article class="event"><div class="event-date">${fmtDate(event.start_date)}${event.end_date&&event.end_date!==event.start_date?' → '+fmtDate(event.end_date):''}</div><h3>${agendaEscape(event.title)}</h3><p>${agendaEscape(agendaSummary(event.summary))}</p><a href="${url}">Voir la fiche agenda →</a></article>`;
      }).join('');
    });
  }catch(error){roots.forEach(root=>{root.innerHTML='<p>Les prochains événements sont disponibles sur <a href="https://agenda.vivreanyons.fr/">agenda.vivreanyons.fr</a>.</p>';});}
}
function simplifyPontRomanPhotos(){
  if(!location.pathname.includes('/Pont-Roman-de-Nyons'))return;
  const figures=[...document.querySelectorAll('main figure')];
  figures.slice(2).forEach(f=>f.remove());
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



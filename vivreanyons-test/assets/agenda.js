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
async function loadAgenda(){
  const roots=[...document.querySelectorAll('[data-agenda]')];if(!roots.length)return;
  try{
    const response=await fetch(AGENDA_DATA,{cache:'no-store'});if(!response.ok)throw new Error('agenda');
    const data=await response.json();
    roots.forEach(root=>{
      const events=selectAgendaEvents(data.events);
      if(!events.length){root.innerHTML='<p>Aucun événement à venir pour le moment.</p>';return;}
      root.innerHTML=events.map(event=>{
        const url=`https://agenda.vivreanyons.fr/evenements/${slugify(event.title)}-${event.start_date}/`;
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

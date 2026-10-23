/* This page only. The same selection and renderer run at publication and in the browser. */
(function () {
  'use strict';
  const esc = s => String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fold = s => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  function clock(now = new Date()) {
    const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', {timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now).map(x => [x.type,x.value]));
    return {day:`${p.year}-${p.month}-${p.day}`,time:`${p.hour}:${p.minute}`};
  }
  const add = (day,n) => new Date(Date.parse(day+'T12:00:00Z')+n*86400000).toISOString().slice(0,10);
  const pretty = day => new Intl.DateTimeFormat('fr-FR',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(day+'T12:00:00Z'));
  function period(day,key) {
    const dow = new Date(day+'T12:00:00Z').getUTCDay();
    if (key==='today') return [day,day];
    if (key==='week') return [day,add(day,(7-dow)%7)];
    if (key==='weekend') {const sat=add(day,dow===0?-1:6-dow);return [day>sat?day:sat,add(sat,1)];}
    return [day,'9999-12-31'];
  }
  function categories(e) {
    const text=fold([e.title,...(e.categories||[])].join(' '));
    const tags=[];
    if (e.kind==='cinema') tags.push('cinema');
    if (/enfance|jeunesse/.test(text) || (e.film||{}).age) tags.push('children');
    if (/concert/.test(text)) tags.push('concerts');
    if (/marche\b/.test(text)) tags.push('markets');
    if (/exposition/.test(text)) tags.push('exhibitions');
    return tags;
  }
  function normalize(feed,published,prices={}) {
    const seen=new Set();
    return (feed.events||[]).flatMap(e => {
      const url=e.page_url, p=e.practical||{};
      if (e.date_warning || !/^https:\/\/agenda\.vivreanyons\.fr\/evenements\/[^/?#]+\/$/.test(url||'') || !published.includes(url)) return [];
      if (!/^\d{4}-\d{2}-\d{2}$/.test(e.start_date||'') || !/^\d{4}-\d{2}-\d{2}$/.test(e.end_date||e.start_date)) return [];
      if (e.commune && fold(e.commune)!=='nyons') return [];
      const key=fold(e.title).replace(/[^a-z0-9]/g,'')+'|'+e.start_date;
      if(seen.has(url)||seen.has(key)) return [];
      seen.add(url);seen.add(key);
      let place=p.location_name||'';
      if (/^(du |lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)/i.test(place)) place='';
      const price=String(p.price||p.tariff||p.tarifs||prices[url]||'');
      const tags=categories(e);
      if (/^(gratuit[e]?|entree libre|acces libre)([.!;]|$| sur reservation)/.test(fold(price.trim()))) tags.push('free');
      return [{title:e.title,url,start:e.start_date,end:e.end_date||e.start_date,time:e.start_time||'',endTime:e.end_time||'',kind:e.kind||'event',tags,
        place: e.kind==='cinema'?'Cinéma L’Arlequin':place,address:e.kind==='cinema'?'28 place de la Libération, Nyons':p.address||'',
        price,age:(e.film||{}).age||'',sessions:(e.sessions||[]).filter(s=>/^\d{4}-\d{2}-\d{2}$/.test(s.date||'')&&/^([01]\d|2[0-3]):[0-5]\d$/.test(s.time||''))}];
    });
  }
  function select(data,now=new Date(),when='all',tag='all') {
    const c=clock(now),[from,to]=period(c.day,when),upcoming=[],ongoing=[];
    for(const e of data.events) {
      if(tag!=='all'&&!e.tags.includes(tag)) continue;
      if(e.kind==='cinema') {
        const s=e.sessions.filter(s=>s.date>=from&&s.date<=to&&(s.date>c.day||(s.date===c.day&&s.time>=c.time))).sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time))[0];
        if(s) upcoming.push({...e,date:s.date,hour:s.time,key:s.date+'T'+s.time});
      } else if(e.start>=c.day && e.start>=from && e.start<=to && (e.start>c.day||!e.time||e.time>=c.time)) {
        upcoming.push({...e,date:e.start,hour:e.time,key:e.start+'T'+(e.time||'23:59')});
      } else if(e.tags.includes('exhibitions')&&e.start<=c.day&&e.end>=from&&e.start<=to&&(e.end>c.day||!e.endTime||e.endTime>=c.time)) {
        ongoing.push(e);
      }
    }
    upcoming.sort((a,b)=>a.key.localeCompare(b.key)||a.title.localeCompare(b.title,'fr'));
    ongoing.sort((a,b)=>a.end.localeCompare(b.end));
    return {upcoming:upcoming.slice(0,12),ongoing:ongoing.slice(0,3),total:upcoming.length};
  }
  function card(e) {
    const hour=e.hour?e.hour.replace(':',' h '):'Horaire non renseigné';
    const range=e.kind!=='cinema'&&e.end!==e.start;
    const time=e.kind==='cinema'?'Prochaine séance : ':'';
    const end=e.kind!=='cinema'&&e.end===e.start&&e.endTime?' – '+e.endTime.replace(':',' h '):'';
    return `<li class="sortie"><div class="sortie-date"><time datetime="${esc(e.date)}">${esc(pretty(e.date))}</time><span>${esc(time+hour+end)}</span>${range?'<span>Jusqu’au '+esc(pretty(e.end))+'</span>':''}</div><div class="sortie-body"><span class="sortie-town">Nyons${e.kind==='cinema'?' · Cinéma':''}</span><h3><a href="${esc(e.url)}">${esc(e.title)}</a></h3><p>${esc(e.place||(!e.address?'Lieu précis non renseigné':''))}${e.address?'<br>'+esc(e.address):''}</p>${e.age?'<p>'+esc(e.age)+'</p>':''}<p class="sortie-price">${esc(e.price||'Tarif non renseigné — voir la fiche')}</p><a class="sortie-link" href="${esc(e.url)}" aria-label="${esc('Informations pratiques : '+e.title)}">Horaires et détails →</a></div></li>`;
  }
  function render(result) {
    let html=result.upcoming.length?'<ol class="sorties-list">'+result.upcoming.map(card).join('')+'</ol>':'<p class="sorties-empty">Aucun rendez-vous à venir ne correspond à ce choix. Essayez une autre période ou consultez <a href="https://agenda.vivreanyons.fr/evenements/">tout l’agenda de Nyons</a>.</p>';
    if(result.ongoing.length) html+='<section class="sorties-ongoing" aria-labelledby="sorties-ongoing-title"><h3 id="sorties-ongoing-title">Expositions déjà en cours</h3><p>Ces dates indiquent la durée de l’exposition. Vérifiez les jours et heures d’ouverture sur la fiche.</p><ul>'+result.ongoing.map(e=>'<li><a href="'+esc(e.url)+'">'+esc(e.title)+'</a> · du '+esc(pretty(e.start))+' au '+esc(pretty(e.end))+'<br>'+esc(e.place||e.address||'Lieu précis non renseigné')+'</li>').join('')+'</ul></section>';
    return html;
  }
  const api={clock,period,normalize,select,render,pretty};
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  if(typeof document==='undefined') return;
  const root=document.getElementById('sorties-nyons');
  if(!root) return;
  const data=JSON.parse(document.getElementById('manifestations-data').textContent),zone=root.querySelector('[data-sorties-results]'),status=root.querySelector('[data-sorties-status]');
  const controls=root.querySelector('[data-sorties-filters]');
  function update() {
    const when=controls.elements.period.value,tag=controls.elements.category.value;
    const result=select(data,new Date(),when,tag);
    zone.innerHTML=render(result);
    status.textContent=result.upcoming.length+' rendez-vous affiché'+(result.upcoming.length>1?'s':'')+(result.total>12?' · les 12 prochains parmi '+result.total:'')+'.';
  }
  controls.hidden=false;
  for(const option of controls.elements.category.options) {
    if(option.value!=='all'&&!data.events.some(e=>e.tags.includes(option.value))) option.disabled=true;
  }
  controls.addEventListener('change',update);
  controls.addEventListener('reset',()=>setTimeout(update,0));
  update();
  setInterval(update,60000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)update();});
})();

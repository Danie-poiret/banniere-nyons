(function(){
 'use strict';
 const esc=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function stamp(now=new Date()){const p=new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now);const v=k=>p.find(x=>x.type===k).value;return `${v('year')}-${v('month')}-${v('day')}T${v('hour')}:${v('minute')}`;}
 function plus(date,n){const d=new Date(date+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10);}
 function weekend(day){const n=new Date(day+'T12:00:00Z').getUTCDay();const start=plus(day,n===0?-1:(6-n));return[start,plus(start,1)];}
 function select(events,now=new Date()){
  const current=stamp(now),day=current.slice(0,10),[sat,sun]=weekend(day),seen=new Set(),out=[];
  for(const item of events){
   let next={...item};
   if(item.kind==='cinema'){
    const session=(item.sessions||[]).filter(s=>s.date+'T'+s.time>=current).sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time))[0];
    if(!session)continue;
    next.start=session.date;next.end=session.date;next.startTime=session.time;next.endTime='';next.dateTime=session.time;
   }else if((item.end||item.start)+'T'+(item.endTime||'23:59')<=current)continue;
   if(seen.has(item.url))continue;seen.add(item.url);
   next.today=next.start<=day&&next.end>=day;
   next.weekend=next.start<=sun&&next.end>=sat;
   next.order=next.start<day?day+'T00:00':next.start+'T'+(next.startTime||'00:00');
   out.push(next);
  }
  return out.sort((a,b)=>a.order.localeCompare(b.order)||a.title.localeCompare(b.title,'fr'));
 }
 function season(day){const m=Number(day.slice(5,7));return m>=3&&m<=5?'spring':m>=6&&m<=8?'summer':m>=9&&m<=11?'autumn':'winter';}
 const API={select,stamp,weekend,season,esc};
 if(typeof module!=='undefined')module.exports=API;
 if(typeof document==='undefined')return;
 const dataElement=document.querySelector('[data-home-content]');if(!dataElement)return;
 const data=JSON.parse(dataElement.textContent);
 const frDate=date=>new Intl.DateTimeFormat('fr-FR',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(date+'T12:00:00Z'));
 function refresh(){
  const events=select(data.events),root=document.querySelector('[data-home-events]');
  if(root)root.innerHTML=events.slice(0,5).map(e=>{
   const visible=e.start<stamp().slice(0,10)?stamp().slice(0,10):e.start;
   const month=new Intl.DateTimeFormat('fr-FR',{month:'short',timeZone:'UTC'}).format(new Date(visible+'T12:00:00Z'));
   return `<article class="home-event${e.today?' is-today':''}"><div class="home-event-date"><strong>${Number(visible.slice(8))}</strong>${esc(month)}<br>${visible.slice(0,4)}</div><div>${e.today?'<span class="home-badge">Aujourd’hui</span>':e.weekend?'<span class="home-badge">Ce week-end</span>':''}<h3><a href="${esc(e.url)}">${esc(e.title)}</a></h3><p class="home-event-place">${esc(e.place)}${e.place&&e.dateTime?' · ':''}${esc(e.dateTime||frDate(e.start))}</p><p>${esc(e.summary)}</p></div></article>`;
  }).join('')||'<p>Les prochaines dates sont à retrouver dans <a href="https://agenda.vivreanyons.fr/">l’agenda de Nyons</a>.</p>';
  const current=data.seasons[season(stamp().slice(0,10))],s=document.querySelector('[data-home-season]');
  if(s){s.querySelector('h2').textContent=current.title;s.querySelector('[data-home-season-cards]').innerHTML=current.items.map(i=>`<article class="home-season-card"><h3><a href="${esc(i.url)}">${esc(i.title)}</a></h3><p>${esc(i.summary)}</p></article>`).join('');}
  const cinema=events.filter(e=>e.kind==='cinema').slice(0,3);
  const c=document.querySelector('[data-home-cinema]');if(c)c.textContent=cinema.length?'Prochaines séances : '+cinema.map(e=>e.title.replace(/^Cinéma — /,'')+' ('+frDate(e.start)+', '+e.startTime+')').join(' · '):'Le programme et les horaires sont à retrouver sur la fiche du cinéma.';
 }
 refresh();setInterval(refresh,60000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
})();

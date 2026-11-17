(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else {root.NyonsLoto=api;api.mount();}
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const FEED='https://agenda.vivreanyons.fr/agenda.json';
  const months={janvier:1,fevrier:2,mars:3,avril:4,mai:5,juin:6,juillet:7,aout:8,septembre:9,octobre:10,novembre:11,decembre:12};
  const clean=v=>String(v||'').replace(/\s+/g,' ').trim();
  const norm=v=>clean(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function day(value){
    if(!/^\d{4}-\d{2}-\d{2}$/.test(value||''))return '';
    const d=new Date(value+'T12:00:00Z');
    return !Number.isNaN(+d)&&d.toISOString().slice(0,10)===value?value:'';
  }
  function parisClock(now){
    const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now).map(x=>[x.type,x.value]));
    return {day:p.year+'-'+p.month+'-'+p.day,time:p.hour+':'+p.minute};
  }
  const time=v=>/^\d{2}:\d{2}$/.test(v||'')&&v<'24:00'&&v.slice(3)<'60'?v:'';
  function safeLink(value,host){
    try{const u=new URL(value);return u.protocol==='https:'&&u.hostname===host?u.href:'';}catch{return '';}
  }
  function conflict(e){
    if(e.date_conflict||e.needs_confirmation)return true;
    const match=norm(e.summary).match(/\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+(\d{1,2})(?:er)?\s+([a-z]+)/);
    return !!(match&&months[match[2]]&&(+e.start_date.slice(5,7)!==months[match[2]]||+e.start_date.slice(8,10)!==+match[1]));
  }
  function normalize(feed){
    if(!feed||!Array.isArray(feed.events))throw new Error('Agenda illisible');
    const unique=new Map();
    for(const e of feed.events){
      if(e.kind==='cinema'||! /\blotos?\b/.test(norm(e.title)))continue;
      if(e.cancelled||e.canceled||/cancelled|canceled|annul/.test(norm(e.status||e.eventStatus))||/\bannule/.test(norm(e.title)))continue;
      const start=day(e.start_date),end=day(e.end_date||e.start_date);
      if(!start||!end||end<start)continue;
      const url=safeLink(e.page_url,'agenda.vivreanyons.fr');
      if(!url||!new URL(url).pathname.startsWith('/evenements/'))continue;
      const p=e.practical||{};
      const record={title:clean(e.title),start,end,startTime:time(e.start_time),endTime:time(e.end_time),url,
        place:clean(p.location_name),address:clean(p.address),phone:clean(p.phone),
        source:safeLink(e.url,'www.nyons.com'),caution:conflict(e)};
      // The feed is Nyons-specific; reject an explicit foreign postcode.
      const postcode=record.address.match(/\b(\d{5})\b/);
      if(postcode&&postcode[1]!=='26110')continue;
      unique.set(url,record);
    }
    return {events:[...unique.values()],sourceUpdated:clean(feed.updated_at)};
  }
  function select(data,now=new Date()){
    const clock=parisClock(now);
    return (data.events||[]).filter(e=>{
      if(!day(e.start)||!day(e.end)||e.end<clock.day)return false;
      const endTime=e.endTime&&(!e.startTime||e.endTime>=e.startTime)?e.endTime:'23:59';
      return e.end!==clock.day||endTime>=clock.time;
    }).sort((a,b)=>(a.start+(a.startTime||'')).localeCompare(b.start+(b.startTime||''))||a.title.localeCompare(b.title,'fr'));
  }
  function dateLabel(iso){return new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date(iso+'T12:00:00Z'));}
  function schedule(e){let s=dateLabel(e.start);if(e.end!==e.start)s+=' au '+dateLabel(e.end);if(e.startTime)s+=' à '+e.startTime.replace(':',' h ');return s;}
  function nextText(events){
    const next=events.find(e=>!e.caution);
    if(next)return 'Le prochain loto annoncé dans l’agenda est '+next.title+', '+schedule(next)+'. '+[next.place,next.address].filter(Boolean).join(', ')+'. Ouvrez sa fiche pour les conditions et les éventuelles modifications.';
    if(events.length)return 'Une annonce figure dans le calendrier, mais sa date demande confirmation auprès de l’organisateur. Consultez le tableau ci-dessus.';
    return 'Aucun prochain loto ne figure actuellement dans l’agenda de Nyons. Le tableau se complète lorsque de nouvelles annonces sont publiées.';
  }
  function render(events){
    if(!events.length)return '<p class="loto-empty">Aucun prochain loto annoncé dans l’agenda pour le moment. Les nouvelles dates apparaîtront ici lorsqu’elles seront publiées.</p>';
    return '<div class="loto-table-wrap" role="region" aria-label="Prochains lotos de Nyons" tabindex="0"><table><caption>Les prochaines annonces de l’agenda de Nyons</caption><thead><tr><th scope="col">Date et heure</th><th scope="col">Loto</th><th scope="col">Lieu et renseignements</th></tr></thead><tbody>'+events.map(e=>'<tr data-loto-end="'+esc(e.end)+'"><th scope="row"><time datetime="'+esc(e.start)+'">'+esc(schedule(e))+'</time></th><td><a href="'+esc(e.url)+'">'+esc(e.title)+'</a><br><span class="loto-badge'+(e.caution?' caution':'')+'">'+(e.caution?'Date à confirmer':'Annoncé dans l’agenda')+'</span></td><td>'+esc([e.place,e.address].filter(Boolean).join(', ')||'Lieu à préciser auprès de l’organisateur')+(e.phone?'<br><a href="tel:'+esc(e.phone.replace(/[^+\d]/g,''))+'">'+esc(e.phone)+'</a>':'')+(e.caution?'<p class="loto-caution">La date de la fiche et une date du descriptif diffèrent : contactez l’association avant de partir.</p>':'')+'</td></tr>').join('')+'</tbody></table></div>';
  }
  function sourceText(data){
    const date=new Date(data.sourceUpdated||'');
    let text=Number.isNaN(+date)?'Dates reprises de l’agenda de Nyons.':'Agenda mis à jour le '+new Intl.DateTimeFormat('fr-FR',{timeZone:'Europe/Paris',dateStyle:'long',timeStyle:'short'}).format(date)+'.';
    if(data.status==='cached')text+=' Agenda momentanément indisponible : dernières annonces disponibles, dates dépassées écartées.';
    return text;
  }
  function mount(){
    const element=document.querySelector('[data-loto-calendar]');if(!element)return;
    let data;try{data=JSON.parse(document.getElementById('loto-data').textContent);}catch{data={events:[],status:'cached'};}
    const result=element.querySelector('[data-loto-results]'),status=element.querySelector('[data-loto-status]'),source=element.querySelector('[data-loto-source]'),next=document.querySelector('[data-loto-next]');
    function paint(){
      const events=select(data);result.innerHTML=render(events);source.textContent=sourceText(data);
      status.textContent=events.length?events.length+' annonce'+(events.length>1?'s':'')+' de loto à venir.':'Aucun prochain loto annoncé.';
      if(next)next.textContent=nextText(events);
    }
    let refreshing=false;
    async function refresh(){
      if(refreshing)return;refreshing=true;
      try{
        const response=await fetch(FEED,{cache:'no-store',signal:AbortSignal.timeout(12000)});
        if(!response.ok)throw new Error('Source indisponible');
        data={...normalize(await response.json()),status:'available'};
      }catch{data.status='cached';}finally{paint();refreshing=false;}
    }
    paint();refresh();
    element.querySelector('[data-loto-refresh]')?.addEventListener('click',refresh);
    setInterval(paint,60000);setInterval(refresh,300000);
    document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
  }
  return {normalize,select,render,nextText,sourceText,parisClock,conflict,mount};
});

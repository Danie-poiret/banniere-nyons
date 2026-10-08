/* Un seul JSON du site ; horaires solaires calculés localement pour Nyons.
   Équations NOAA : https://gml.noaa.gov/grad/solcalc/solareqns.PDF */
(() => {
  'use strict';
  const section=document.querySelector('[data-nyons-direct]');
  if (!section) return;
  const zone='Europe/Paris', unavailable='Donnée indisponible';
  const dateFormat=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit'});
  const clock=new Intl.DateTimeFormat('fr-FR',{timeZone:zone,hour:'2-digit',minute:'2-digit'});
  const stamp=new Intl.DateTimeFormat('fr-FR',{timeZone:zone,day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
  function dayKey(now) {
    const parts=Object.fromEntries(dateFormat.formatToParts(now).map(p=>[p.type,p.value]));
    return parts.year+'-'+parts.month+'-'+parts.day;
  }
  function sunTimes(key) {
    const midnight=Date.parse(key+'T00:00:00Z');
    const year=Number(key.slice(0,4));
    const days=(Date.UTC(year+1,0,1)-Date.UTC(year,0,1))/86400000;
    const ordinal=(midnight-Date.UTC(year,0,1))/86400000+1;
    const radians=Math.PI/180, latitude=44.36*radians;
    // Fractional-year approximation at noon; zenith 90.833° includes refraction.
    const gamma=2*Math.PI/days*(ordinal-1);
    const eq=229.18*(.000075+.001868*Math.cos(gamma)-.032077*Math.sin(gamma)-.014615*Math.cos(2*gamma)-.040849*Math.sin(2*gamma));
    const decl=.006918-.399912*Math.cos(gamma)+.070257*Math.sin(gamma)-.006758*Math.cos(2*gamma)+.000907*Math.sin(2*gamma)-.002697*Math.cos(3*gamma)+.00148*Math.sin(3*gamma);
    const angle=Math.acos(Math.cos(90.833*radians)/(Math.cos(latitude)*Math.cos(decl))-Math.tan(latitude)*Math.tan(decl))/radians;
    const noon=720-4*5.14-eq;
    return {rise:new Date(midnight+Math.round(noon-4*angle)*60000),set:new Date(midnight+Math.round(noon+4*angle)*60000)};
  }
  let data=null,lastAttempt=0,running=false;
  function render() {
    const now=Date.now(),today=dayKey(new Date(now));
    for (const key of ['air','river','fire','water']) {
      const card=section.querySelector('[data-direct-card="'+key+'"]');
      const item=data && data.items && data.items[key];
      const expires=item && Date.parse(item.validUntil);
      const checked=item && Date.parse(item.checkedAt);
      const valid=item && item.status==='available' && typeof item.label==='string' &&
        Number.isFinite(expires) && Number.isFinite(checked) && expires>now &&
        checked<=now+300000 && now-checked<12*3600000 &&
        (!(key==='air'||key==='fire') || item.date===today);
      card.dataset.state=valid?'available':'unavailable';
      card.querySelector('[data-direct-value]').textContent=valid?item.label:unavailable;
      card.querySelector('[data-direct-note]').textContent=valid?(item.detail||''):
        item && item.status==='unavailable' && typeof item.detail==='string'?item.detail:
        'Consulte la source officielle.';
    }
    const solar=section.querySelector('[data-direct-card="sun"]'),times=sunTimes(today);
    const duration=Math.round((times.set-times.rise)/60000);
    solar.querySelector('[data-direct-value]').textContent='Lever '+clock.format(times.rise)+' · coucher '+clock.format(times.set);
    solar.querySelector('[data-direct-note]').textContent='Durée du jour : '+Math.floor(duration/60)+' h '+String(duration%60).padStart(2,'0')+' · '+stamp.format(new Date(today+'T12:00:00Z')).split(' ')[0];
    solar.dataset.state='available';solar.dataset.solarDate=today;
    const update=section.querySelector('[data-direct-updated]');
    const collected=data && Date.parse(data.collectedAt);
    update.textContent=Number.isFinite(collected) && collected<=now+300000?
      'Dernière mise à jour : '+stamp.format(new Date(collected))+(now-collected>12*3600000?' · actualisation en attente':''):
      'Dernière mise à jour : donnée indisponible';
  }
  async function load() {
    if (running) return;
    running=true;lastAttempt=Date.now();
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000);
    try {
      const response=await fetch(section.dataset.directUrl,{signal:controller.signal,credentials:'same-origin',cache:'no-cache'});
      if (!response.ok) throw new Error('Données absentes');
      const result=await response.json();
      if (result.schemaVersion!==1 || result.commune!=='26220' || !result.items) throw new Error('Données invalides');
      data=result;section.dataset.directState='ready';
    } catch (_) { data=null;section.dataset.directState='error'; }
    finally { clearTimeout(timer);running=false;render(); }
  }
  render();load();
  // Recalcul du jour et expiration sans nouvelles requêtes.
  setInterval(()=>{if (!document.hidden) render();},60000);
  document.addEventListener('visibilitychange',()=>{
    if (!document.hidden) {render();if (Date.now()-lastAttempt>3*3600000) load();}
  });
})();

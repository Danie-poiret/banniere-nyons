/* Données fixes de Nyons, sans géolocalisation ni service tiers dans le navigateur. */
(() => {
  'use strict';
  const module = document.querySelector('[data-nyons-weather]');
  if (!module) return;
  const find = name => module.querySelector('[data-weather-' + name + ']');
  const status = find('status'), content = find('content'), button = find('refresh');
  const zone = 'Europe/Paris';
  const clock = new Intl.DateTimeFormat('fr-FR', {timeZone:zone,hour:'2-digit',minute:'2-digit'});
  const dateLabel = new Intl.DateTimeFormat('fr-FR', {timeZone:zone,day:'numeric',month:'long'});
  const shortLabel = new Intl.DateTimeFormat('fr-FR', {timeZone:zone,weekday:'short',day:'numeric',month:'short'});
  const hourNumber = new Intl.DateTimeFormat('en-GB',{timeZone:zone,hour:'2-digit',hourCycle:'h23'});
  const number = new Intl.NumberFormat('fr-FR', {maximumFractionDigits:1});
  const keyFormat = new Intl.DateTimeFormat('en-CA', {timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit'});
  function dayKey(date) {
    const parts = Object.fromEntries(keyFormat.formatToParts(date).map(p => [p.type,p.value]));
    return parts.year + '-' + parts.month + '-' + parts.day;
  }
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const temperature = value => finite(value) ? Math.round(value) + ' °C' : '—';
  const speed = value => finite(value) ? Math.round(value * 3.6) + ' km/h' : '—';
  function condition(symbol) {
    if (typeof symbol !== 'string') return ['🌡️','Conditions indisponibles'];
    const night = symbol.endsWith('_night');
    const name = symbol.replace(/_(day|night|polartwilight)$/,'');
    if (name.includes('thunder')) return ['⛈️','Orages'];
    if (name.includes('sleet')) return ['🌨️','Pluie et neige'];
    if (name.includes('snow')) return ['❄️',name.includes('showers') ? 'Averses de neige' : 'Neige'];
    if (name.includes('rain')) return [name.includes('showers') ? '🌦️' : '🌧️', name.includes('showers') ? 'Averses' : 'Pluie'];
    const known = {clearsky:[night?'🌙':'☀️',night?'Ciel dégagé':'Ensoleillé'],fair:[night?'🌙':'🌤️','Peu nuageux'],partlycloudy:['⛅','Éclaircies'],cloudy:['☁️','Nuageux'],fog:['🌫️','Brouillard']};
    return known[name] || ['🌡️','Conditions indisponibles'];
  }
  function node(tag, className, text) {
    const element = document.createElement(tag);
    element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }
  let running = false, lastAttempt = 0;
  async function load() {
    if (running) return;
    running = true; lastAttempt = Date.now();
    button.disabled = true;
    status.textContent = 'Actualisation de la météo…';
    module.setAttribute('aria-busy','true');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(),12000);
    try {
      const response = await fetch(module.dataset.weatherUrl, {signal:controller.signal,cache:'no-cache',credentials:'same-origin'});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const forecast = await response.json();
      const now = Date.now();
      if (forecast.location !== 'Nyons' || !Array.isArray(forecast.timeseries)) throw new Error('Données invalides');
      const collected = Date.parse(forecast.collectedAt);
      const updated = Date.parse(forecast.modelUpdatedAt);
      if (!Number.isFinite(collected) || !Number.isFinite(updated) || now-collected>12*3600000 || collected-now>3600000) throw new Error('Données trop anciennes');
      const series = forecast.timeseries.filter(item => Number.isFinite(Date.parse(item.time)) && item.data && item.data.instant && item.data.instant.details).sort((a,b) => Date.parse(a.time)-Date.parse(b.time));
      if (!series.length) throw new Error('Prévisions absentes');
      const current = series.reduce((best,item) => Math.abs(Date.parse(item.time)-now)<Math.abs(Date.parse(best.time)-now) ? item : best);
      if (Math.abs(Date.parse(current.time)-now)>90*60000 || !finite(current.data.instant.details.air_temperature)) throw new Error('Température absente');
      const detail = current.data.instant.details;
      const period = current.data.next_1_hours || current.data.next_6_hours;
      const [icon,label] = condition(period && period.summary && period.summary.symbol_code);
      find('icon').textContent = icon;
      find('temp').textContent = temperature(detail.air_temperature);
      find('condition').textContent = label;
      find('hour').textContent = 'Estimation à ' + clock.format(new Date(current.time));
      find('wind').textContent = speed(detail.wind_speed);
      find('humidity').textContent = finite(detail.relative_humidity) ? Math.round(detail.relative_humidity) + ' %' : '—';
      const directions=['Nord','Nord-est','Est','Sud-est','Sud','Sud-ouest','Ouest','Nord-ouest'];
      find('direction').textContent = finite(detail.wind_from_direction) ? directions[Math.round(((detail.wind_from_direction%360)+360)%360/45)%8] : '—';
      const rain = period && period.details && period.details.precipitation_amount;
      find('rain-label').textContent = current.data.next_1_hours ? 'Pluie · prochaine heure' : 'Pluie · prochaines 6 h';
      find('rain').textContent = finite(rain) ? number.format(rain) + ' mm' : '—';
      const today = dayKey(new Date(now));
      const base = new Date(today + 'T12:00:00Z');
      const days = [];
      for (let index=0; index<5; index++) {
        const date = new Date(base.getTime()+index*86400000), key = dayKey(date);
        const points = series.filter(item => dayKey(new Date(item.time))===key && (index!==0 || Date.parse(item.time)>=Date.parse(current.time)));
        if (!points.length) throw new Error('Journée manquante');
        const values=[], winds=[];
        for (const item of points) {
          const d=item.data.instant.details;
          if (finite(d.air_temperature)) values.push(d.air_temperature);
          if (finite(d.wind_speed)) winds.push(d.wind_speed);
          const next=item.data.next_6_hours;
          if (next && next.details && dayKey(new Date(Date.parse(item.time)+6*3600000))===key) {
            if (finite(next.details.air_temperature_min)) values.push(next.details.air_temperature_min);
            if (finite(next.details.air_temperature_max)) values.push(next.details.air_temperature_max);
          }
        }
        const midday = points.reduce((best,item) => {
          const distance = point => Math.abs(Number(hourNumber.format(new Date(point.time)))-12);
          return distance(item)<distance(best) ? item : best;
        });
        const summary = midday.data.next_1_hours || midday.data.next_6_hours || midday.data.next_12_hours;
        const [dayIcon,dayCondition]=condition(summary && summary.summary && summary.summary.symbol_code);
        const li=node('li','weather-day');
        const time=node('time','',index===0?'Aujourd’hui':index===1?'Demain':shortLabel.format(date)); time.dateTime=key;
        li.append(time);
        const image=node('span','weather-day-icon',dayIcon); image.setAttribute('aria-hidden','true'); li.append(image);
        li.append(node('span','weather-day-condition',dayCondition));
        li.append(node('span','weather-range',values.length?Math.round(Math.min(...values))+'° à '+Math.round(Math.max(...values))+'°':'—'));
        li.append(node('span','weather-wind','Vent jusqu’à '+(winds.length?speed(Math.max(...winds)):'—')));
        days.push(li);
      }
      find('days').replaceChildren(...days);
      content.hidden=false;
      status.textContent='Prévisions mises à jour le ' + dateLabel.format(new Date(updated)) + ' à ' + clock.format(new Date(updated)) + (now-collected>6*3600000?' · actualisation en attente':'');
      module.dataset.weatherState='ready';
    } catch (error) {
      content.hidden=true;
      status.textContent='La météo est momentanément indisponible. Réessaie ou consulte le bulletin Météo-France ci-dessous.';
      module.dataset.weatherState='error';
    } finally {
      clearTimeout(timeout); running=false; button.disabled=false;
      module.setAttribute('aria-busy','false');
    }
  }
  button.hidden=false;
  button.addEventListener('click',load);
  document.addEventListener('visibilitychange',() => {if (!document.hidden && Date.now()-lastAttempt>10*60000) load();});
  setInterval(() => {if (!document.hidden) load();},10*60000);
  load();
})();

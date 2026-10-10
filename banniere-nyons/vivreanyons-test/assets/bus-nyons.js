(function () {
  'use strict';
  const DAY = 86400;
  function offset(date, days) { const d = new Date(date + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + days); return d.toISOString().slice(0, 10); }
  function active(service, day) {
    if (!service) return false;
    const date = day.replace(/-/g, '');
    if (service.removed.includes(date)) return false;
    if (service.added.includes(date)) return true;
    const weekday = (new Date(day + 'T12:00:00Z').getUTCDay() + 6) % 7;
    return date >= service.start && date <= service.end && service.week[weekday] === 1;
  }
  function usable(source, date, now) {
    return source && ['available', 'cached'].includes(source.status) &&
      Number.isFinite(Date.parse(source.checkedAt)) && now - Date.parse(source.checkedAt) >= -300000 && now - Date.parse(source.checkedAt) <= 3 * DAY * 1000 &&
      date.replace(/-/g, '') >= source.start && date.replace(/-/g, '') <= source.end;
  }
  function query(data, options, now = Date.now()) {
    const rows = [], seen = new Set(), inbound = options.sense === 'in';
    for (const trip of data.trips) {
      const route = data.routes[trip.route];
      if (!route || (options.line && trip.route !== options.line) || !usable(data.sources[route.source], options.date, now)) continue;
      for (const shift of [0, -1, -2]) {
        if (!active(data.services[trip.service], offset(options.date, shift))) continue;
        trip.stops.forEach((stop, index) => {
          const nyons = data.stops[stop[0]];
          const event = (inbound ? stop[1] : stop[2]) + shift * DAY;
          if (!nyons.nyons || (options.stop && options.stop !== stop[0]) || event < 0 || event >= DAY || (inbound ? stop[4] : stop[3]) === 1) return;
          const candidates = trip.stops.map((s, i) => ({ s, i, place: data.stops[s[0]] })).filter(x =>
            !x.place.nyons && (inbound ? x.i < index : x.i > index) &&
            (inbound ? x.s[3] : x.s[4]) !== 1 && (!options.city || x.place.city === options.city));
          const partner = inbound ? candidates[0] : candidates[candidates.length - 1];
          if (!partner) return;
          const from = inbound ? partner.s : stop, to = inbound ? stop : partner.s;
          const depart = from[2] + shift * DAY, arrive = to[1] + shift * DAY;
          const key = [trip.route, from[0], to[0], depart, arrive].join('|');
          if (seen.has(key)) return;
          seen.add(key);
          rows.push({ line: route.number, route: trip.route, from: data.stops[from[0]], to: data.stops[to[0]], depart, arrive, event,
            reservation: from[3] >= 2 || to[4] >= 2 });
        });
      }
    }
    return rows.sort((a, b) => a.event - b.event || a.depart - b.depart || a.line.localeCompare(b.line));
  }
  function time(seconds) {
    const value = ((seconds % DAY) + DAY) % DAY, h = Math.floor(value / 3600), m = Math.floor(value % 3600 / 60);
    return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0') + (seconds < 0 ? ' (veille)' : seconds >= DAY ? ' (lendemain)' : '');
  }
  function parisDate(now = new Date()) {
    const parts = new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(now);
    return ['year', 'month', 'day'].map(k => parts.find(p => p.type === k).value).join('-');
  }
  function escape(value) { return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
  const api = { active, query, time, offset, parisDate, usable, escape };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof document === 'undefined') return;
  const box = document.querySelector('[data-bus-schedules]');
  if (!box) return;
  const date = box.querySelector('[data-bus-date]'), line = box.querySelector('[data-bus-line]'), sense = box.querySelector('[data-bus-sense]'),
    stop = box.querySelector('[data-bus-stop]'), city = box.querySelector('[data-bus-city]'), results = box.querySelector('[data-bus-results]'), status = box.querySelector('[data-bus-status]');
  let data;
  date.value = parisDate(); date.min = offset(date.value, -7); date.max = offset(date.value, 120);
  function options(select, entries, first) {
    const previous = select.value;
    select.innerHTML = '<option value="">' + escape(first) + '</option>' + entries.map(([value, label]) => '<option value="' + escape(value) + '">' + escape(label) + '</option>').join('');
    if (entries.some(x => x[0] === previous)) select.value = previous;
  }
  function filters() {
    const related = data.trips.filter(t => !line.value || t.route === line.value);
    const ids = new Set(related.flatMap(t => t.stops.map(s => s[0])));
    options(stop, [...ids].filter(i => data.stops[i].nyons).map(i => [i, data.stops[i].name + ' · ' + data.sources[data.routes[related.find(t => t.stops.some(s => s[0] === i)).route].source].label]), 'Tous les arrêts de Nyons');
    const cities = [...new Set([...ids].filter(i => !data.stops[i].nyons).map(i => data.stops[i].city))].sort((a, b) => a.localeCompare(b, 'fr'));
    options(city, cities.map(c => [c, c]), sense.value === 'in' ? 'Toutes les provenances' : 'Toutes les destinations');
    box.querySelector('[data-bus-city-label]').textContent = sense.value === 'in' ? 'Provenance' : 'Destination';
  }
  function render() {
    if (!data || !/^\d{4}-\d{2}-\d{2}$/.test(date.value)) return;
    const rows = query(data, { date: date.value, line: line.value, sense: sense.value, stop: stop.value, city: city.value });
    const sources = line.value ? [data.routes[line.value].source] : Object.keys(data.sources);
    const missing = sources.filter(k => !usable(data.sources[k], date.value, Date.now()));
    const cached = sources.filter(k => data.sources[k].status === 'cached');
    const dates = sources.map(k => Date.parse(data.sources[k].checkedAt)).filter(Number.isFinite);
    let message = dates.length ? 'Données vérifiées le ' + new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', dateStyle: 'short', timeStyle: 'short' }).format(Math.min(...dates)) + '. Actualisation quotidienne.' : 'Données actuellement indisponibles.';
    if (missing.length) message += ' Horaires non disponibles pour cette date : ' + missing.map(k => data.sources[k].label).join(', ') + '. Consultez les fiches officielles ci-dessous.';
    if (cached.length) message += ' Derniers horaires conservés pendant une interruption de la source : ' + cached.map(k => data.sources[k].label).join(', ') + '.';
    status.textContent = message;
    if (!rows.length) {
      results.innerHTML = '<p class="bus-empty">' + (missing.length === sources.length ? 'Les horaires officiels ne sont pas disponibles pour cette date.' : 'Aucun trajet trouvé pour cette date et ces filtres. Essayez un autre jour, un autre arrêt ou une autre destination.') + '</p>';
      return;
    }
    const place = p => '<span>' + escape(p.city) + '</span><small>' + escape(p.name) + '</small>';
    results.innerHTML = '<p class="bus-count">' + rows.length + ' passage' + (rows.length > 1 ? 's' : '') + ' à Nyons · ' +
      new Intl.DateTimeFormat('fr-FR', { dateStyle: 'full', timeZone: 'UTC' }).format(new Date(date.value + 'T12:00:00Z')) + '</p>' +
      '<div class="bus-table-scroll" tabindex="0" role="region" aria-label="Tableau des horaires"><table><caption>' + (sense.value === 'in' ? 'Trajets vers Nyons' : 'Trajets au départ de Nyons') +
      '</caption><thead><tr><th scope="col">Ligne</th><th scope="col">Départ</th><th scope="col">Arrivée</th></tr></thead><tbody>' + rows.map(r =>
        '<tr><th scope="row">' + escape(r.line) + (r.reservation ? '<small>Sur réservation</small>' : '') + '</th><td><strong>' + time(r.depart) + '</strong>' + place(r.from) +
        '</td><td><strong>' + time(r.arrive) + '</strong>' + place(r.to) + '</td></tr>').join('') + '</tbody></table></div>';
  }
  const sourceUrl = new URL('../assets/bus-nyons.json', document.currentScript.src);
  fetch(sourceUrl, { cache: 'no-store' }).then(r => { if (!r.ok) throw new Error('unavailable'); return r.json(); }).then(value => {
    if (value.version !== 1 || !Array.isArray(value.trips)) throw new Error('invalid');
    data = value;
    const routes = Object.entries(data.routes).sort((a, b) => a[1].number.localeCompare(b[1].number, 'fr', { numeric: true }));
    options(line, routes.map(([id, r]) => [id, r.number + ' · ' + r.name]), 'Toutes les lignes');
    [date, line, sense, stop, city].forEach(field => { field.disabled = false; field.addEventListener('change', () => { if (field === line || field === sense) filters(); render(); }); });
    filters(); render();
  }).catch(() => { status.textContent = 'Les horaires ne peuvent pas être chargés pour le moment.'; results.innerHTML = '<p>Retrouvez les horaires sur les sites officiels indiqués ci-dessous.</p>'; });
})();

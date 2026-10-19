/* Carte des marchés de la Drôme. Données locales sourcées, aucun suivi utilisateur. */
(() => {
  'use strict';
  const root = document.querySelector('[data-markets-guide]');
  if (!root) return;
  const search = root.querySelector('#market-search');
  const day = root.querySelector('#market-day');
  const period = root.querySelector('#market-period');
  const count = root.querySelector('#market-count');
  const feedback = root.querySelector('#market-map-status');
  const cards = [...root.querySelectorAll('[data-market-id]')];
  const normal = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr');
  const escape = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  let records = [], map, layer;
  const empty = root.querySelector('#market-empty');
  function update() {
    const needle = normal(search.value.trim());
    const shown = records.filter(row => normal(row.commune+' '+row.nom+' '+row.lieu).includes(needle) && (!day.value || row.jours.includes(day.value)) && (!period.value || row.saisonnalite === period.value));
    const ids = new Set(shown.map(row => row.id));
    cards.forEach(card => { card.hidden = !ids.has(card.dataset.marketId); });
    const towns = new Set(shown.map(row => row.commune));
    count.textContent = `${shown.length} marché${shown.length > 1 ? 's' : ''} · ${towns.size} commune${towns.size > 1 ? 's' : ''}`;
    empty.hidden = shown.length > 0;
    if (!layer) return;
    layer.clearLayers();
    const groups = new Map();
    shown.forEach(row => { if (!groups.has(row.code_insee)) groups.set(row.code_insee, []); groups.get(row.code_insee).push(row); });
    groups.forEach(rows => {
      const row = rows[0];
      const marker = L.circleMarker([row.latitude,row.longitude], {radius:11,weight:2,color:'#fff',fillColor:'#4c6344',fillOpacity:1});
      const content = `<div class="market-popup"><h3>${escape(row.commune)}</h3><p class="market-popup-note">Repère communal. Adresses dans les fiches.</p>${rows.map(item => `<p><strong>${escape(item.nom)}</strong><br>${escape(item.jours.join(' et '))} · ${escape(item.horaires || 'Horaires non publiés')}<br>${escape(item.lieu)}<br>${escape(item.periode)}${item.note?'<br>'+escape(item.note):''}<br><a href="#marche-${escape(item.id)}">Voir la fiche</a></p>`).join('')}</div>`;
      marker.bindPopup(content, {maxWidth:300}).bindTooltip(`${row.commune} — ${rows.length} marché${rows.length>1?'s':''}`);
      marker.on('add', () => { const el=marker.getElement(); if (el) { el.setAttribute('tabindex','0'); el.setAttribute('role','button'); el.setAttribute('aria-label',`Marchés à ${row.commune}, ouvrir les informations`); } });
      marker.on('keypress', event => { if (event.originalEvent.key === 'Enter' || event.originalEvent.key === ' ') marker.openPopup(); });
      marker.addTo(layer);
    });
    if (groups.size) { const points=[...groups.values()].map(rows => [rows[0].latitude,rows[0].longitude]); map.fitBounds(points,{padding:[35,35],maxZoom:10,animate:false}); }
  }
  fetch('/assets/marches-drome/marches-verifies.json', {credentials:'omit'})
    .then(response => { if (!response.ok) throw Error('Données indisponibles'); return response.json(); })
    .then(data => {
      records=data.marches;
      root.querySelector('#market-filters').hidden=false;
      if (window.L) {
        root.querySelector('#market-map').hidden=false;
        map=L.map('market-map',{scrollWheelZoom:false,zoomControl:true});
        let loaded=false;
        const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'});
        tiles.on('tileload',()=>{loaded=true; feedback.textContent='Zoomez avec les boutons. Cliquez sur une commune pour lire ses marchés.';});
        tiles.on('tileerror',()=>{if(!loaded) feedback.textContent='Le fond de carte est indisponible. Les fiches et les filtres restent utilisables.';});
        tiles.addTo(map); layer=L.layerGroup().addTo(map);
      } else { root.querySelector('#market-map').hidden=true; feedback.textContent='La carte ne peut pas se charger. Les fiches et les filtres restent utilisables.'; }
      [search,day,period].forEach(field=>field.addEventListener(field===search?'input':'change',update));
      root.querySelector('#market-reset').addEventListener('click',()=>{search.value='';day.value='';period.value='';update();});
      update();
    }).catch(()=>{feedback.textContent='La carte et les filtres sont momentanément indisponibles. Toutes les fiches restent lisibles ci-dessous.';root.querySelector('#market-map').hidden=true;});
})();

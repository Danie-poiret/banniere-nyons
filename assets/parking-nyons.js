(() => {
  'use strict';
  const guide = document.querySelector('.parking-guide');
  if (!guide) return;
  const rows = [...guide.querySelectorAll('[data-parking-tags]')];
  const filters = guide.querySelector('.parking-filters');
  const search = guide.querySelector('#parking-search');
  const result = guide.querySelector('#parking-results');
  const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  let filter = 'all';
  function refreshRows() {
    const query = normalize(search.value.trim());
    let count = 0;
    rows.forEach(row => {
      const match = (filter === 'all' || row.dataset.parkingTags.split(' ').includes(filter)) && normalize(row.textContent).includes(query);
      row.hidden = !match;
      if (match) count++;
    });
    result.textContent = `${count} parking${count > 1 ? 's' : ''} affiché${count > 1 ? 's' : ''}${count === 0 ? ' — essaie un autre nom ou « Tous ».' : ''}`;
  }
  filters.hidden = false;
  search.addEventListener('input', refreshRows);
  guide.querySelectorAll('[data-parking-filter]').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.parkingFilter;
    guide.querySelectorAll('[data-parking-filter]').forEach(other => other.setAttribute('aria-pressed', String(other === button)));
    refreshRows();
  }));
  const mapElement = guide.querySelector('#parking-map');
  const loadButton = guide.querySelector('#parking-load-map');
  const status = guide.querySelector('#parking-map-status');
  let mapPromise;
  let map;
  const pins = new Map();
  const escape = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  function loadStyles() {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
      link.crossOrigin = '';
      link.onload = resolve;
      link.onerror = () => { link.remove(); reject(new Error('Styles de carte indisponibles')); };
      document.head.appendChild(link);
    });
  }
  function loadLibrary() {
    return new Promise((resolve, reject) => {
      if (window.L) return resolve();
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
      script.crossOrigin = '';
      script.onload = resolve;
      script.onerror = () => { script.remove(); reject(new Error('Bibliothèque de carte indisponible')); };
      document.head.appendChild(script);
    });
  }
  function loadMap() {
    if (mapPromise) return mapPromise;
    loadButton.disabled = true;
    status.textContent = 'Chargement de la carte…';
    mapPromise = (async () => {
      const [response] = await Promise.all([fetch('/assets/parking-nyons-data.json?v=20261012-v1'), loadStyles(), loadLibrary()]);
      if (!response.ok) throw new Error('Repères indisponibles');
      const places = await response.json();
      mapElement.hidden = false;
      map = window.L.map(mapElement, {scrollWheelZoom:false});
      let tileFailed = false;
      window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom:19,
        attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'
      }).on('tileerror', () => {
        tileFailed = true;
        status.textContent = 'Le fond de carte est momentanément indisponible. Le tableau et les itinéraires restent utilisables.';
      }).on('load', () => {
        if (!tileFailed) status.textContent = 'Clique sur un point pour voir le parking ou le secteur. Les places libres ne sont pas mesurées en direct.';
      }).addTo(map);
      places.forEach(place => {
        const icon = window.L.divIcon({className:'',html:`<span style="display:block" class="parking-dot ${escape(place.kind)}"></span>`,iconSize:[22,22],iconAnchor:[11,11]});
        const type = place.kind === 'secteur' ? 'Repère de secteur' : place.kind === 'camper' ? 'Aire camping-cars' : 'Parking identifié';
        const destination = place.kind === 'secteur' ? encodeURIComponent(`${place.name} Nyons`) : `${place.lat},${place.lon}`;
        const url = place.kind === 'secteur' ? `https://www.google.com/maps/search/?api=1&query=${destination}` : `https://www.google.com/maps/dir/?api=1&destination=${destination}`;
        const marker = window.L.marker([place.lat,place.lon], {icon,title:place.name,alt:place.name,keyboard:true}).bindPopup(`<div class="parking-map-popup"><strong>${escape(place.name)}</strong>${escape(place.info)}<span class="parking-small">${type} · capacité indicative, sans disponibilité en direct.</span><a href="${escape(url)}" target="_blank" rel="noopener noreferrer">${place.kind === 'secteur' ? 'Rechercher l’itinéraire' : 'Ouvrir l’itinéraire'} ↗</a></div>`).addTo(map);
        pins.set(place.id,marker);
      });
      map.fitBounds(places.map(place => [place.lat,place.lon]), {padding:[26,26]});
      loadButton.textContent = 'Recentrer la carte';
      loadButton.disabled = false;
      status.textContent = 'Carte affichée : 11 repères de parkings, de secteurs et de l’aire camping-cars.';
      return map;
    })().catch(error => {
      if (map) { map.remove(); map = null; pins.clear(); }
      mapElement.hidden = true;
      mapPromise = null;
      loadButton.disabled = false;
      loadButton.textContent = 'Réessayer d’afficher la carte';
      status.textContent = 'La carte ne peut pas être chargée pour le moment. Utilise le tableau et ses liens d’itinéraire ci-dessous.';
      throw error;
    });
    return mapPromise;
  }
  loadButton.addEventListener('click', () => {
    if (map) { map.fitBounds([...pins.values()].map(pin => pin.getLatLng()), {padding:[26,26]}); return; }
    loadMap().catch(() => {});
  });
  guide.querySelectorAll('[data-parking-pin]').forEach(button => button.addEventListener('click', async () => {
    try {
      await loadMap();
      const marker = pins.get(button.dataset.parkingPin);
      if (marker) { map.setView(marker.getLatLng(),16); marker.openPopup(); mapElement.scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',block:'center'}); }
    } catch (_) { loadButton.focus(); }
  }));
})();

(() => {
 'use strict';
 const form=document.getElementById('hike-filters');if(!form)return;
 let records;try{records=JSON.parse(document.getElementById('hike-data').textContent);}catch{document.getElementById('hike-map-status').textContent='La carte est indisponible. Toutes les fiches restent lisibles ci-dessous.';return;}
 const cards=[...document.querySelectorAll('[data-hike-id]')],count=document.getElementById('hike-count'),status=document.getElementById('hike-map-status');
 const fields=Object.fromEntries(['search','difficulty','duration','distance','commune','type','family'].map(k=>[k,document.getElementById('hike-'+k)]));
 const norm=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr');
 const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let map,layer,markers=new Map();
 const bound=(value,mode,low,high)=>!mode||(mode==='short'?value<low:mode==='medium'?value>=low&&value<=high:value>high);
 function matches(r){return norm(r.name+' '+r.commune+' '+r.start).includes(norm(fields.search.value.trim()))&&(!fields.difficulty.value||r.difficulty===fields.difficulty.value)&&bound(r.duration_max,fields.duration.value,120,240)&&bound(r.distance_km_max,fields.distance.value,5,10)&&(!fields.commune.value||r.commune===fields.commune.value)&&(!fields.type.value||r.route_type===fields.type.value)&&(!fields.family.checked||r.family_documented===true);}
 function popup(r){return '<div class="hg-popup"><h3>'+escape(r.name)+'</h3><p>'+escape(r.commune)+' · '+escape(r.difficulty_label)+'<br>'+r.distance_km_min+(r.distance_km_max!==r.distance_km_min?' à '+r.distance_km_max:'')+' km · '+r.duration_min+(r.duration_max!==r.duration_min?' à '+r.duration_max:'')+' min · +'+r.ascent_m+' m</p><p><strong>Départ à pied :</strong> '+escape(r.start)+'<br><strong>Stationnement :</strong> '+escape(r.parking||'Aucun parking précis confirmé.')+'<br>Le marqueur n’est pas une place de parking.</p><p><a href="#rando-'+r.id+'">Voir la fiche ci-dessous</a> · <a href="'+escape(r.article)+'">Guide détaillé</a><br><a href="https://www.google.com/maps/dir/?api=1&amp;destination='+r.lat+','+r.lon+'&amp;travelmode=walking" target="_blank" rel="noopener">Rejoindre le départ à pied ↗</a><br><a href="'+escape(r.gpx)+'">GPX officiel ↗</a></p></div>';}
 function update(){
  const shown=records.filter(matches),ids=new Set(shown.map(r=>r.id));cards.forEach(c=>c.hidden=!ids.has(c.dataset.hikeId));
  count.textContent=shown.length+' randonnée'+(shown.length>1?'s':'')+' dans la liste';document.getElementById('hike-empty').hidden=shown.length>0;
  if(!layer)return;layer.clearLayers();markers.clear();shown.forEach(r=>{
   const marker=L.marker([r.lat,r.lon],{icon:L.divIcon({className:'hg-marker '+r.difficulty,html:'<span>'+r.number+'</span>',iconSize:[44,44],iconAnchor:[22,22]}),title:r.name,alt:'Départ '+r.number+' : '+r.name,keyboard:true}).bindPopup(popup(r),{maxWidth:300});marker.addTo(layer);markers.set(r.id,marker);
  });
  if(shown.length){map.fitBounds(shown.map(r=>[r.lat,r.lon]),{padding:[35,35],maxZoom:14,animate:false});status.textContent=shown.length+' départs affichés. Cliquez sur un numéro pour consulter le guide.';}
  else{map.closePopup();status.textContent='Aucun départ ne correspond aux filtres. Cliquez sur Tout afficher pour revoir les circuits.';}
 }
 form.hidden=false;form.addEventListener('submit',e=>e.preventDefault());Object.values(fields).forEach(f=>f.addEventListener(f.type==='search'?'input':'change',update));
 form.addEventListener('reset',()=>{Object.values(fields).forEach(f=>{if(f.type==='checkbox')f.checked=false;else f.value='';});update();});
 if(window.L){
  try{
   document.getElementById('hike-map').hidden=false;map=L.map('hike-map',{scrollWheelZoom:false});layer=L.layerGroup().addTo(map);
   let loaded=false;const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'});
   tiles.on('tileload',()=>{loaded=true;status.textContent='Zoomez avec les boutons, puis cliquez sur un numéro. Les filtres mettent à jour la carte et les fiches.';});
   tiles.on('tileerror',()=>{if(!loaded)status.textContent='Le fond de carte est indisponible. Les départs, les fiches et leurs liens restent utilisables.';});tiles.addTo(map);
   document.querySelectorAll('[data-locate]').forEach(b=>{b.hidden=false;b.addEventListener('click',()=>{const marker=markers.get(b.dataset.locate);if(!marker)return;document.getElementById('carte-departs').scrollIntoView({block:'start'});map.invalidateSize();map.setView(marker.getLatLng(),15,{animate:false});marker.openPopup();});});
  }catch{document.getElementById('hike-map').hidden=true;status.textContent='La carte ne peut pas se charger. Les fiches et les filtres restent utilisables.';}
 }
 update();
})();

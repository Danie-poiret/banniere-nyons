(() => {
 'use strict';
 const root=document.getElementById('cn-filters');if(!root)return;
 const records=JSON.parse(document.getElementById('cn-data').textContent),cards=[...document.querySelectorAll('[data-place]')];
 const search=document.getElementById('cn-search'),category=document.getElementById('cn-category'),count=document.getElementById('cn-count'),status=document.getElementById('cn-status'),enable=document.getElementById('cn-map-enable');
 const views=[...root.querySelectorAll('[data-view]')],norm=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr');
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let view='center',map,layer,markers=new Map(),tilesLoaded=false;
 function popup(r){return '<div class="cn-popup"><h3>'+esc(r.name)+'</h3><p>'+esc(r.description)+'</p><p class="cn-precision">'+esc(r.precision)+'</p><p>'+(r.article?'<a href="'+esc(r.article)+'">Lire la fiche de Vivre à Nyons →</a><br>':'')+'<a href="#lieu-'+r.id+'">Voir les détails et la source</a></p></div>';}
 function update(){
  const query=norm(search.value.trim());
  const shown=records.filter(r=>(view==='all'||r.center)&&(!category.value||r.category===category.value)&&norm(r.name+' '+r.description+' '+r.categoryLabel).includes(query));
  const ids=new Set(shown.map(r=>r.id));cards.forEach(c=>c.hidden=!ids.has(c.dataset.place));
  count.textContent=shown.length+' lieu'+(shown.length>1?'x':'')+' · '+(view==='center'?'Centre historique':'Nyons et ses quartiers');
  document.getElementById('cn-empty').hidden=shown.length>0;views.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
  if(!map)return;layer.clearLayers();markers.clear();map.closePopup();
  shown.forEach(r=>{const m=L.marker([r.lat,r.lon],{icon:L.divIcon({className:'cn-marker '+r.category,html:'<span>'+r.number+'</span>',iconSize:[44,44],iconAnchor:[22,22]}),title:r.name,alt:r.number+' : '+r.name,keyboard:true}).bindPopup(popup(r),{maxWidth:300});m.addTo(layer);markers.set(r.id,m);});
  if(shown.length)map.fitBounds(shown.map(r=>[r.lat,r.lon]),{padding:[38,38],maxZoom:view==='center'?16:15,animate:false});
  status.textContent=shown.length?'Clique sur un numéro pour ouvrir sa fiche. Les repères ne certifient pas une entrée ou un accès automobile.':'Aucun repère ne correspond aux filtres. Essaie « Tout réafficher ».';
 }
 function loadMap(){
  if(map)return true;
  if(!window.L){status.textContent='Le plan ne peut pas se charger. La liste des lieux et les liens restent utilisables.';return false;}
  try{
   const node=document.getElementById('cn-map');node.hidden=false;map=L.map(node,{scrollWheelZoom:false});layer=L.layerGroup().addTo(map);
   const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'});
   tiles.on('tileload',()=>{tilesLoaded=true;});tiles.on('tileerror',()=>{if(!tilesLoaded)status.textContent='Le fond de carte est indisponible. Les repères et les fiches restent utilisables.';});tiles.addTo(map);
   document.getElementById('cn-map-intro').hidden=true;update();return true;
  }catch{status.textContent='La carte est indisponible. Consulte les lieux dans la liste.';document.getElementById('cn-map').hidden=true;return false;}
 }
 root.hidden=false;enable.hidden=false;root.addEventListener('submit',e=>e.preventDefault());
 search.addEventListener('input',update);category.addEventListener('change',update);
 views.forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;update();}));
 root.addEventListener('reset',()=>{search.value='';category.value='';view='all';update();});
 enable.addEventListener('click',loadMap);
 document.querySelectorAll('[data-locate]').forEach(b=>{b.hidden=false;b.addEventListener('click',()=>{if(!loadMap())return;const marker=markers.get(b.dataset.locate);if(!marker)return;document.getElementById('carte-nyons').scrollIntoView({block:'start'});map.invalidateSize();map.setView(marker.getLatLng(),17,{animate:false});marker.openPopup();});});
 update();
})();

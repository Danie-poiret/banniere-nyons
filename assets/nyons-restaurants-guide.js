(function(){
 'use strict';
 const root=document.querySelector('.food-map-section');
 if(!root)return;
 const container=root.querySelector('#food-restaurants-map');
 const status=root.querySelector('#food-map-status');
 const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let places=[];try{places=JSON.parse(root.querySelector('[data-food-places]').textContent);}catch(_){}
 const count=places.length;
 const fail=()=>{container.hidden=true;status.textContent='La carte ne peut pas être chargée pour le moment. Ouvre la liste des '+count+' adresses ci-dessous : les fiches et les itinéraires restent utilisables.';};
 if(!window.L){fail();return;}
 let map;
 try{
  if(!count){fail();return;}
  container.hidden=false;
  map=window.L.map(container,{scrollWheelZoom:false,zoomControl:false,zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false}).setView([44.3606,5.1419],17);
  window.L.control.zoom({position:'bottomleft'}).addTo(map);
  map.on('popupopen',event=>{
   const frame=container.getBoundingClientRect(),box=event.popup.getElement().getBoundingClientRect(),padding=12;
   const dx=box.left<frame.left+padding?box.left-frame.left-padding:box.right>frame.right-padding?box.right-frame.right+padding:0;
   const dy=box.top<frame.top+padding?box.top-frame.top-padding:box.bottom>frame.bottom-padding?box.bottom-frame.bottom+padding:0;
   if(dx||dy)map.panBy([dx,dy],{animate:false});
  });
  let tileFailed=false;
  window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
   maxZoom:19,
   attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>'
  }).on('tileerror',()=>{
   tileFailed=true;
   status.textContent='Le fond de carte est momentanément indisponible. Les repères, les adresses et les itinéraires de la liste restent accessibles.';
  }).on('load',()=>{if(!tileFailed)status.textContent=count+' repères disponibles. Clique sur un numéro ou utilise la liste des adresses.'+(places.some(p=>p.outside)?' « Toutes les adresses » inclut les Laurons et Condorcet.':'');}).addTo(map);
  const markers=new Map();
  places.forEach((place,index)=>{
   const destination=encodeURIComponent(place.name+', '+place.address);
   const direction='https://www.google.com/maps/dir/?api=1&destination='+destination;
   const icon=window.L.divIcon({className:'',html:'<span class="food-map-pin'+(place.id==='Cuisine-du-Marche'||place.id==='Crepe-au-sud'?' is-uncertain':'')+'">'+(index+1)+'</span>',iconSize:[24,24],iconAnchor:[12,12],popupAnchor:[0,-12]});
   const detail=place.fiche?'<a href="'+escape(place.fiche)+'">Lire la fiche sur Vivre à Nyons →</a>':'<a href="'+escape(place.source)+'" target="_blank" rel="noopener noreferrer">Fiche de l’office de tourisme →</a>';
   const popup='<div class="food-map-popup"><strong>'+escape(place.name)+'</strong><p>'+escape(place.address)+'</p><p>'+escape(place.note)+'</p>'+detail+'<a href="'+escape(direction)+'" target="_blank" rel="noopener noreferrer">Itinéraire Google Maps ↗</a></div>';
   const marker=window.L.marker([place.lat,place.lon],{icon,title:(index+1)+'. '+place.name,alt:place.name,keyboard:true,riseOnHover:true}).bindPopup(popup,{maxWidth:Math.min(260,container.clientWidth-80),autoPan:false}).addTo(map);
   marker.getElement().setAttribute('aria-label',(index+1)+'. '+place.name);
   markers.set(place.id,marker);
  });
  root.querySelector('.food-map-toolbar').hidden=false;
  root.querySelector('[data-food-center]').addEventListener('click',()=>map.setView([44.3606,5.1419],17));
  root.querySelector('[data-food-all]').addEventListener('click',()=>map.fitBounds(places.map(p=>[p.lat,p.lon]),{padding:[30,30]}));
  root.querySelectorAll('[data-food-pin]').forEach(button=>{
   button.hidden=false;
   button.addEventListener('click',()=>{
    const marker=markers.get(button.dataset.foodPin);
    if(!marker)return;
    map.setView(marker.getLatLng(),18,{animate:false});marker.openPopup();
    container.scrollIntoView({behavior:'instant',block:'center'});
   });
  });
  container.dataset.ready='true';
  status.textContent=count+' repères disponibles. Clique sur un numéro ou ouvre la liste des adresses. Les horaires ne sont pas vérifiés en temps réel.';
 }catch(_){if(map)map.remove();fail();}
})();

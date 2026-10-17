(()=>{'use strict';
  const sections=[...document.querySelectorAll('[data-balade-map]')];
  if(!sections.length)return;
  let library;
  function leaflet(){
    if(window.L)return Promise.resolve();
    if(library)return library;
    library=Promise.all([
      ['link','https://unpkg.com/leaflet@1.9.4/dist/leaflet.css','sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY='],
      ['script','https://unpkg.com/leaflet@1.9.4/dist/leaflet.js','sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=']
    ].map(([tag,url,integrity])=>new Promise((resolve,reject)=>{
      const el=document.createElement(tag);
      if(tag==='link'){el.rel='stylesheet';el.href=url;}else el.src=url;
      el.integrity=integrity;el.crossOrigin='anonymous';
      const timer=setTimeout(()=>{el.remove();reject(Error('timeout'));},15000);
      el.onload=()=>{clearTimeout(timer);resolve();};
      el.onerror=()=>{clearTimeout(timer);el.remove();reject(Error('load'));};
      document.head.append(el);
    }))).catch(error=>{library=undefined;throw error;});
    return library;
  }
  sections.forEach(section=>{
    const data=JSON.parse(section.querySelector('[data-map-data]').textContent);
    const load=section.querySelector('[data-map-load]');
    const canvas=section.querySelector('[data-map-canvas]');
    const status=section.querySelector('[data-map-status]');
    const reset=section.querySelector('[data-map-reset]');
    let map,bounds,markers=[];
    load.hidden=false;
    function fit(){map.fitBounds(bounds,{padding:[30,30],maxZoom:16});}
    function popup(point,index){
      const box=document.createElement('div');box.className='balade-map-popup';
      const title=document.createElement('strong');title.textContent=(index+1)+'. '+point.name;
      const info=document.createElement('p');info.textContent=point.info;
      const link=document.createElement('a');link.textContent='Ouvrir ce repère sur OpenStreetMap';
      link.href='https://www.openstreetmap.org/?mlat='+point.lat+'&mlon='+point.lon+'#map=17/'+point.lat+'/'+point.lon;
      link.target='_blank';link.rel='noopener noreferrer';box.append(title,info,link);return box;
    }
    load.addEventListener('click',async()=>{
      if(map){fit();return;}
      load.disabled=true;status.textContent='Chargement de la carte…';
      try{
        await leaflet();canvas.hidden=false;
        map=L.map(canvas,{scrollWheelZoom:false});
        const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
          maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        bounds=L.latLngBounds([]);
        if(data.route){
          const line=L.polyline(data.route,{color:'#426b37',weight:5,opacity:.9}).addTo(map);
          line.bindTooltip('Tracé du GPX municipal des Bois de Lumière');bounds.extend(line.getBounds());
        }
        data.points.forEach((point,index)=>{
          const pin=document.createElement('span');pin.textContent=String(index+1);pin.className='balade-map-pin';
          const icon=L.divIcon({className:'balade-map-icon',html:pin,iconSize:[32,32],iconAnchor:[16,16]});
          const marker=L.marker([point.lat,point.lon],{icon,title:point.name,alt:point.name,keyboard:true}).addTo(map).bindPopup(popup(point,index));
          markers.push(marker);bounds.extend([point.lat,point.lon]);
        });
        L.control.scale({imperial:false}).addTo(map);fit();
        reset.hidden=false;load.hidden=true;
        section.querySelector('[data-map-intro]').hidden=true;
        status.textContent=data.route?'Le tracé vert suit le GPX municipal. Le repère 1 indique le départ au col de la Croix.':'Cliquez sur un numéro pour découvrir le lieu. Les points sont des repères de localisation.';
        tiles.on('tileerror',()=>{status.textContent='Le fond de carte est partiellement indisponible. Les repères et les liens ci-dessous restent utilisables.';});
        section.querySelectorAll('[data-map-point]').forEach(button=>{
          button.hidden=false;button.addEventListener('click',()=>{
            const marker=markers[Number(button.dataset.mapPoint)];
            map.setView(marker.getLatLng(),17);marker.openPopup();canvas.focus({preventScroll:true});
          });
        });
        reset.addEventListener('click',()=>{map.closePopup();fit();});
      }catch(error){
        if(map){map.remove();map=undefined;markers=[];}canvas.hidden=true;
        load.disabled=false;load.hidden=false;load.textContent='Réessayer d’afficher la carte';
        status.textContent='La carte ne peut pas être chargée. Les liens de localisation et les documents officiels restent disponibles ci-dessous.';
      }
    });
  });
})();


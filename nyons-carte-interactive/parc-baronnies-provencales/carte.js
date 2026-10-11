(() => {
  'use strict';
  const svg=document.getElementById('baronnies-map');
  const plane=document.getElementById('map-plane');
  const villages=JSON.parse(document.getElementById('map-data').textContent);
  const markers=[...svg.querySelectorAll('.village-marker')];
  const view={zoom:1,x:0,y:0};
  let drag=null,moved=false;
  function render(){
    plane.setAttribute('transform',`translate(${view.x} ${view.y}) scale(${view.zoom})`);
    const pixel=1100/(svg.getBoundingClientRect().width||1100)/view.zoom;
    markers.forEach(m=>{m.querySelector('circle').setAttribute('r',11*pixel);m.querySelector('text').setAttribute('font-size',11*pixel);});
    document.getElementById('zoom-out').disabled=view.zoom<=1;
    document.getElementById('zoom-in').disabled=view.zoom>=8;
  }
  function zoomBy(factor){const z=Math.min(8,Math.max(1,view.zoom*factor));const r=z/view.zoom;view.x=550-(550-view.x)*r;view.y=325-(325-view.y)*r;view.zoom=z;render();}
  function focusVillage(number,recenter=false){
    const v=villages.find(v=>v.number===Number(number));if(!v)return;
    markers.forEach(m=>m.classList.toggle('is-selected',Number(m.dataset.village)===v.number));
    document.getElementById('selected-name').textContent=v.name;
    document.getElementById('selected-detail').textContent=`Repère ${v.number} · centre géographique de la commune. La fiche permet de poursuivre la découverte.`;
    const a=document.getElementById('selected-link');a.textContent=`Lire la fiche de ${v.name}`;a.href=v.url;a.hidden=false;
    if(recenter){view.zoom=4;view.x=550-v.point[0]*4;view.y=325-v.point[1]*4;render();}
  }
  document.getElementById('zoom-in').addEventListener('click',()=>zoomBy(1.5));
  document.getElementById('zoom-out').addEventListener('click',()=>zoomBy(1/1.5));
  document.getElementById('map-reset').addEventListener('click',()=>{Object.assign(view,{zoom:1,x:0,y:0});render();});
  document.getElementById('map-nyons').addEventListener('click',()=>focusVillage(1,true));
  document.getElementById('park-visible').addEventListener('change',e=>{document.getElementById('park-outline').style.display=e.target.checked?'':'none';});
  markers.forEach(m=>{
    m.addEventListener('click',()=>{if(!moved)focusVillage(m.dataset.village);});
    m.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();focusVillage(m.dataset.village);}});
  });
  document.querySelectorAll('[data-focus]').forEach(b=>b.addEventListener('click',()=>{focusVillage(b.dataset.focus,true);svg.scrollIntoView({block:'center',behavior:'smooth'});svg.focus({preventScroll:true});}));
  function point(e){const rect=svg.getBoundingClientRect();const factor=Math.min(rect.width/1100,rect.height/650);return [(e.clientX-rect.left-(rect.width-1100*factor)/2)/factor,(e.clientY-rect.top-(rect.height-650*factor)/2)/factor];}
  svg.addEventListener('pointerdown',e=>{if(e.button!==0)return;const p=point(e);drag={id:e.pointerId,p,x:view.x,y:view.y};moved=false;});
  svg.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;const p=point(e);if(Math.hypot(p[0]-drag.p[0],p[1]-drag.p[1])>5){moved=true;svg.setPointerCapture(e.pointerId);}if(moved){view.x=drag.x+p[0]-drag.p[0];view.y=drag.y+p[1]-drag.p[1];render();}});
  svg.addEventListener('pointerup',()=>{drag=null;});svg.addEventListener('pointercancel',()=>{drag=null;});
  svg.addEventListener('wheel',e=>{if(e.ctrlKey){e.preventDefault();zoomBy(e.deltaY<0?1.15:1/1.15);}},{passive:false});
  svg.addEventListener('keydown',e=>{const delta=60;if(['+','=','-','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();if(e.key==='+'||e.key==='=')zoomBy(1.5);else if(e.key==='-')zoomBy(1/1.5);else{if(e.key==='ArrowLeft')view.x+=delta;if(e.key==='ArrowRight')view.x-=delta;if(e.key==='ArrowUp')view.y+=delta;if(e.key==='ArrowDown')view.y-=delta;render();}}});
  const normalize=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  document.getElementById('village-search').addEventListener('input',e=>{const q=normalize(e.target.value.trim());let count=0;document.querySelectorAll('.village-card').forEach(c=>{c.hidden=!normalize(c.dataset.name).includes(q);if(!c.hidden)count++;});document.getElementById('search-empty').hidden=count>0;});
  window.addEventListener('resize',render);
  if(window.matchMedia('(max-width:600px)').matches)focusVillage(1,true);else render();
})();

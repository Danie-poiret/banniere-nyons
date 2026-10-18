/* Shared historical photo viewer; follows the native-dialog pattern of the existing galleries. */
(function(){
  'use strict';
  if(document.querySelector('#memory-photo-viewer')||typeof HTMLDialogElement==='undefined')return;
  const images=[...document.querySelectorAll('main .page-photo img,main article figure img,main .photo-stack img,main .feature-media img')]
    .filter(img=>!img.closest('.right-sidebar,.memory-card,[data-pont-gallery],[data-arcades-gallery]'));
  if(!images.length)return;
  const script=document.currentScript;
  const css=document.createElement('link');css.rel='stylesheet';
  css.href=new URL('memory-photo-viewer.css?v=20261018-v1',script.src).href;document.head.append(css);
  const dialog=document.createElement('dialog');dialog.id='memory-photo-viewer';dialog.className='memory-photo-viewer';
  dialog.setAttribute('aria-label','Agrandir les photographies historiques');
  dialog.innerHTML='<div class="mp-shell"><div class="mp-toolbar"><span class="mp-counter" role="status" aria-live="polite"></span><button type="button" class="mp-close" aria-label="Fermer la photo">✕</button><button type="button" class="mp-prev" aria-label="Photo précédente">←</button><button type="button" class="mp-next" aria-label="Photo suivante">→</button><button type="button" class="mp-minus" aria-label="Réduire le zoom">−</button><button type="button" class="mp-plus" aria-label="Agrandir le zoom">+</button><button type="button" class="mp-reset" aria-label="Afficher la photo entière">Ajuster</button><a class="mp-original" target="_blank" rel="noopener">Original ↗</a></div><div class="mp-stage" tabindex="0" role="region" aria-label="Photo agrandie ; flèches pour la déplacer après zoom"><img class="mp-image" alt="" draggable="false"></div><div class="mp-caption"><p class="mp-text"></p><div class="mp-help">Zoom : + / − ou molette. Déplacement : glisser la photo. Sur écran tactile : pincer avec deux doigts. Échap pour fermer.</div></div></div>';
  document.body.append(dialog);
  const find=selector=>dialog.querySelector(selector);
  const stage=find('.mp-stage'),image=find('.mp-image'),caption=find('.mp-text'),counter=find('.mp-counter');
  const close=find('.mp-close'),previous=find('.mp-prev'),next=find('.mp-next'),minus=find('.mp-minus'),plus=find('.mp-plus'),reset=find('.mp-reset');
  let index=0,origin=null,zoom=1,x=0,y=0,fit=1,scrollX=0,scrollY=0,previousOverflow='',previousPadding='';
  let gesture=null,loadNumber=0;
  const pointers=new Map();
  function fullSource(img){
    const explicit=img.getAttribute('data-full-src')||img.getAttribute('data-original');
    if(explicit)return new URL(explicit,document.baseURI).href;
    const link=img.closest('a[href]');
    if(link&&/\.(?:png|jpe?g|webp|avif|gif)(?:[?#]|$)/i.test(link.href))return link.href;
    const candidates=(img.getAttribute('srcset')||'').split(',').map(s=>s.trim().split(/\s+/)).filter(a=>a.length===2);
    if(candidates.length){candidates.sort((a,b)=>parseFloat(b[1])-parseFloat(a[1]));return new URL(candidates[0][0],document.baseURI).href;}
    return img.currentSrc||img.src;
  }
  function render(){
    if(!image.naturalWidth||!stage.clientWidth||!image.hasAttribute('data-loaded'))return;
    const width=stage.clientWidth,height=stage.clientHeight;
    fit=Math.min(width/image.naturalWidth,height/image.naturalHeight,1);
    x=Math.max(-Math.max(0,(image.naturalWidth*fit*zoom-width)/2),Math.min(Math.max(0,(image.naturalWidth*fit*zoom-width)/2),x));
    y=Math.max(-Math.max(0,(image.naturalHeight*fit*zoom-height)/2),Math.min(Math.max(0,(image.naturalHeight*fit*zoom-height)/2),y));
    image.style.width=image.naturalWidth+'px';image.style.height=image.naturalHeight+'px';
    image.style.transform='translate(-50%,-50%) translate('+x+'px,'+y+'px) scale('+(fit*zoom)+')';
    stage.dataset.zoom=zoom.toFixed(2);minus.disabled=zoom<=1;plus.disabled=zoom>=6;
  }
  function setZoom(value,anchorX=0,anchorY=0){
    const old=zoom;zoom=Math.min(6,Math.max(1,value));
    x=anchorX-(anchorX-x)*zoom/old;y=anchorY-(anchorY-y)*zoom/old;render();
  }
  function show(value){
    index=(value+images.length)%images.length;zoom=1;x=0;y=0;pointers.clear();gesture=null;
    const thumb=images[index],src=fullSource(thumb),token=++loadNumber;
    image.removeAttribute('data-loaded');image.alt=thumb.alt;
    caption.textContent=thumb.closest('figure')?.querySelector('figcaption')?.textContent.trim()||thumb.alt||'Photographie historique';
    counter.textContent='Photo '+(index+1)+' sur '+images.length;
    find('.mp-original').href=src;
    previous.hidden=next.hidden=images.length<2;
    image.onload=()=>{if(token!==loadNumber)return;image.setAttribute('data-loaded','');render();};
    image.onerror=()=>{if(token===loadNumber)counter.textContent='Photo indisponible — ouvrir le lien Original';};
    image.src=src;
    if(image.complete&&image.naturalWidth){image.setAttribute('data-loaded','');render();}
  }
  images.forEach((thumb,i)=>{
    thumb.setAttribute('data-memory-photo','');
    const link=thumb.closest('a');
    const trigger=link||thumb;
    if(!link){thumb.tabIndex=0;thumb.setAttribute('role','button');}
    trigger.setAttribute('aria-haspopup','dialog');
    trigger.setAttribute('aria-label','Agrandir : '+(thumb.alt||'photographie historique'));
    function open(event){
      if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
      event.preventDefault();origin=trigger;scrollX=window.scrollX;scrollY=window.scrollY;
      previousOverflow=document.body.style.overflow;previousPadding=document.body.style.paddingRight;
      const gutter=window.innerWidth-document.documentElement.clientWidth;
      if(gutter>0)document.body.style.paddingRight=(parseFloat(getComputedStyle(document.body).paddingRight)||0)+gutter+'px';
      document.body.style.overflow='hidden';dialog.showModal();show(i);close.focus({preventScroll:true});
    }
    trigger.addEventListener('click',open);
    if(!link)trigger.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){open(event);}});
  });
  close.addEventListener('click',()=>dialog.close());
  previous.addEventListener('click',()=>show(index-1));next.addEventListener('click',()=>show(index+1));
  plus.addEventListener('click',()=>setZoom(zoom*1.5));minus.addEventListener('click',()=>setZoom(zoom/1.5));
  reset.addEventListener('click',()=>{zoom=1;x=y=0;render();});
  dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
  dialog.addEventListener('keydown',event=>{
    if(event.key==='+'||event.key==='='){event.preventDefault();setZoom(zoom*1.5);}
    if(event.key==='-'){event.preventDefault();setZoom(zoom/1.5);}
    if(event.key==='0'){event.preventDefault();zoom=1;x=y=0;render();}
    if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;
    event.preventDefault();
    if(zoom>1){if(event.key==='ArrowLeft')x+=50;if(event.key==='ArrowRight')x-=50;if(event.key==='ArrowUp')y+=50;if(event.key==='ArrowDown')y-=50;render();}
    else if(event.key==='ArrowLeft')show(index-1);else if(event.key==='ArrowRight')show(index+1);
  });
  stage.addEventListener('wheel',event=>{
    event.preventDefault();const box=stage.getBoundingClientRect();
    setZoom(zoom*Math.exp(-Math.sign(event.deltaY)*.18),event.clientX-box.left-box.width/2,event.clientY-box.top-box.height/2);
  },{passive:false});
  function measure(){
    const points=[...pointers.values()];
    if(points.length>1)return {cx:(points[0].x+points[1].x)/2,cy:(points[0].y+points[1].y)/2,d:Math.hypot(points[0].x-points[1].x,points[0].y-points[1].y)};
    return points.length?{cx:points[0].x,cy:points[0].y,d:0}:null;
  }
  stage.addEventListener('pointerdown',event=>{
    if(event.pointerType==='mouse'&&event.button!==0)return;
    stage.setPointerCapture(event.pointerId);pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});gesture=measure();
  });
  stage.addEventListener('pointermove',event=>{
    if(!pointers.has(event.pointerId))return;
    pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});const current=measure();
    if(gesture){
      if(current.d&&gesture.d){const box=stage.getBoundingClientRect();setZoom(zoom*current.d/gesture.d,current.cx-box.left-box.width/2,current.cy-box.top-box.height/2);}
      x+=current.cx-gesture.cx;y+=current.cy-gesture.cy;render();
    }
    gesture=current;
  });
  function release(event){pointers.delete(event.pointerId);gesture=measure();}
  stage.addEventListener('pointerup',release);stage.addEventListener('pointercancel',release);stage.addEventListener('lostpointercapture',release);
  stage.addEventListener('dblclick',event=>{const box=stage.getBoundingClientRect();setZoom(zoom>1?1:2,event.clientX-box.left-box.width/2,event.clientY-box.top-box.height/2);});
  dialog.addEventListener('close',()=>{
    loadNumber++;pointers.clear();gesture=null;image.removeAttribute('src');image.removeAttribute('data-loaded');
    document.body.style.overflow=previousOverflow;document.body.style.paddingRight=previousPadding;
    if(origin?.isConnected)origin.focus({preventScroll:true});
    window.scrollTo({left:scrollX,top:scrollY,behavior:'instant'});
  });
  new ResizeObserver(()=>{if(dialog.open)render();}).observe(stage);
})();

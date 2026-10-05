/* Photos du Pont Roman de Nyons : agrandissement au clavier et à la souris. */
(function(){
  const links=[...document.querySelectorAll('[data-pont-gallery]')];
  const dialog=document.querySelector('#pont-photo-viewer');
  if(!links.length||!dialog||typeof dialog.showModal!=='function')return;
  const image=dialog.querySelector('.pont-full-image');
  const caption=dialog.querySelector('.pont-full-caption');
  const counter=dialog.querySelector('.pont-photo-counter');
  const close=dialog.querySelector('[data-photo-close]');
  let index=0,origin=null;
  function show(next){
    index=(next+links.length)%links.length;
    const link=links[index],thumb=link.querySelector('img');
    image.src=link.href;image.alt=thumb.alt;
    caption.textContent=link.closest('figure').querySelector('figcaption').textContent;
    counter.textContent='Photo '+(index+1)+' sur '+links.length;
  }
  links.forEach((link,i)=>link.addEventListener('click',event=>{
    if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
    event.preventDefault();origin=link;show(i);
    dialog.showModal();document.body.classList.add('pont-photo-open');close.focus();
  }));
  close.addEventListener('click',()=>dialog.close());
  dialog.querySelector('[data-photo-prev]').addEventListener('click',()=>show(index-1));
  dialog.querySelector('[data-photo-next]').addEventListener('click',()=>show(index+1));
  dialog.addEventListener('keydown',event=>{
    if(event.key==='ArrowLeft'){event.preventDefault();show(index-1);}
    if(event.key==='ArrowRight'){event.preventDefault();show(index+1);}
  });
  dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
  dialog.addEventListener('close',()=>{
    document.body.classList.remove('pont-photo-open');
    image.removeAttribute('src');
    if(origin&&origin.isConnected)origin.focus();
  });
})();

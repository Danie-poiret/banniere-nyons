/* Historical recommendations use the existing city registry and live city indexes. */
(async function installMemorySidebar(){
  'use strict';
  const ownScript=document.currentScript;
  const root=new URL('../',ownScript.src);
  const article=document.querySelector('main article:not(.card)');
  if(!article||document.querySelector('[data-memory-sidebar]'))return;
  const canonical=document.querySelector('link[rel="canonical"]');
  if(!canonical)return;
  const current=new URL(canonical.href).pathname;
  const localPath=location.pathname.slice(root.pathname.length).replace(/index\.html$/,'');
  if(current!=='/'+localPath)return;
  const local=path=>new URL(path.replace(/^\//,''),root).href;
  async function get(path,type){
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),10000);
    try{
      const response=await fetch(local(path),{signal:controller.signal,credentials:'same-origin'});
      if(!response.ok)throw new Error('Historical navigation unavailable');
      return type==='json'?await response.json():await response.text();
    }finally{clearTimeout(timer);}
  }
  try{
    const registry=await get('tools/memory-cities.json','json');
    const route=path=>registry.cities.find(city=>
      city.legacy.some(row=>'/'+row.path.replace(/index\.html$/,'')===path)||
      (path.startsWith('/'+city.path+'/')&&path.split('/').filter(Boolean).length===4));
    const city=route(current);
    if(!city)return;
    const layout=article.parentElement;
    layout.setAttribute('data-memory-history-layout','');
    let sidebar=layout.querySelector(':scope > aside.right-sidebar');
    if(!sidebar){sidebar=document.createElement('aside');sidebar.className='right-sidebar';layout.classList.add('has-sidebar');}
    // These are the shared tourism cards. Keep the table of contents and bespoke historical cards.
    const tourism=new Set(['Plein air','Culture','Gastronomie','Alentours','Les rendez-vous','Infos pratiques']);
    [...sidebar.children].forEach(card=>{
      const title=card.querySelector(':scope > .side-title');
      if(title&&tourism.has(title.textContent.trim()))card.remove();
    });
    sidebar.setAttribute('aria-label','Navigation historique de Mémoire de France');
    sidebar.classList.add('memory-history-sidebar');
    sidebar.setAttribute('data-memory-sidebar','');
    // DOM order puts the recommendations after the full article on mobile.
    layout.append(sidebar);
    const stylesheet=document.createElement('link');stylesheet.rel='stylesheet';
    stylesheet.href=new URL('memory-sidebar.css?v=20261021-v1',ownScript.src).href;
    document.head.append(stylesheet);
    const panel=document.createElement('section');panel.className='side-card memory-history-card';
    const heading=document.createElement('h2');heading.className='memory-history-title';
    heading.textContent='🏛️ À découvrir aussi à '+city.name;
    const related=document.createElement('nav');related.setAttribute('aria-label','Autres histoires de '+city.name);
    const list=document.createElement('ul');list.className='memory-history-links';related.append(list);
    const explore=document.createElement('nav');explore.className='memory-history-explore';explore.setAttribute('aria-label','Explorer Mémoire de France');
    const parts=city.path.split('/');
    const link=(name,path)=>{const anchor=document.createElement('a');anchor.href=local(path);anchor.textContent=name;return anchor;};
    explore.append(link('Explorer le département : '+city.department,'/'+parts.slice(0,2).join('/')+'/'),link('Explorer la région : '+city.region,'/'+parts[0]+'/'),link('Découvrir toutes les histoires de Mémoire de France','/memoire-de-france/'));
    panel.append(heading,related,explore);sidebar.prepend(panel);
    const stories=new Map();
    const checked=new Set(),available=new Map();
    async function validateLinks(){
      while(available.size<5){
        const batch=[...stories.values()].filter(story=>!checked.has(story.path)).slice(0,5-available.size);
        if(!batch.length)break;
        await Promise.all(batch.map(async story=>{
          checked.add(story.path);
          const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000);
          try{
            const response=await fetch(local(story.path),{method:'HEAD',signal:controller.signal,credentials:'same-origin'});
            if(response.ok)available.set(story.path,story);
          }catch(error){/* Never recommend an unavailable destination. */}
          finally{clearTimeout(timer);}
        }));
      }
    }
    async function addCity(candidate){
      try{
        const source=await get(candidate.path+'/');
        const page=new DOMParser().parseFromString(source,'text/html');
        page.querySelectorAll('main article.card a[href]').forEach(anchor=>{
          const url=new URL(anchor.getAttribute('href'),'https://www.vivreanyons.fr/'+candidate.path+'/');
          if(url.origin!=='https://www.vivreanyons.fr'||url.search||url.hash)return;
          const owner=route(url.pathname);
          const title=anchor.querySelector('h2,h3');
          if(!owner||owner.path!==candidate.path||url.pathname===current||!title||!title.textContent.trim())return;
          stories.set(url.pathname,{path:url.pathname,title:title.textContent.trim(),city:owner.name});
        });
      }catch(error){/* Other existing city indexes can still supply recommendations. */}
    }
    await addCity(city);
    await validateLinks();
    const department=parts.slice(0,2).join('/');
    const nearby=registry.cities.filter(other=>other.path!==city.path&&other.path.startsWith(department+'/'));
    const regional=registry.cities.filter(other=>other.path.split('/')[0]===parts[0]&&other.path!==city.path&&!nearby.includes(other));
    if(available.size<3){
      for(const other of [...nearby,...regional]){await addCity(other);await validateLinks();if(available.size>=5)break;}
    }
    // Preserve index order even when the availability responses arrive out of order.
    for(const story of [...stories.values()].filter(story=>available.has(story.path)).slice(0,5)){
      const item=document.createElement('li');const anchor=link(story.title,story.path);
      if(story.city!==city.name){const place=document.createElement('span');place.className='memory-history-place';place.textContent=story.city;anchor.append(place);}
      item.append(anchor);list.append(item);
    }
    if(!list.children.length){
      related.replaceChildren(link('Retrouver les histoires de '+city.name,'/'+city.path+'/'));
    }
    panel.setAttribute('data-memory-sidebar-ready','');
  }catch(error){/* A registry failure never changes another section of the site. */}
})();

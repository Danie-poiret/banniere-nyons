(function(){
 const section=document.querySelector('[data-restaurant-directory]');if(!section)return;
 const cards=[...section.querySelectorAll('[data-restaurant-card]')],input=section.querySelector('input'),buttons=[...section.querySelectorAll('[data-restaurant-filter]')],count=section.querySelector('[data-restaurant-count]'),empty=section.querySelector('[data-restaurant-empty]');
 let selected='all';const normalize=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[’']/g,' ');
 const texts=cards.map(card=>normalize(card.textContent));
 function update(){const query=normalize(input.value.trim());let found=0;cards.forEach((card,i)=>{const matches=(selected==='all'||card.dataset.tags.split(' ').includes(selected))&&query.split(/\s+/).every(word=>texts[i].includes(word));card.hidden=!matches;if(matches)found++;});count.textContent=found+' adresse'+(found>1?'s':'')+' affichée'+(found>1?'s':'');empty.hidden=found!==0;buttons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.restaurantFilter===selected)));}
 input.addEventListener('input',update);buttons.forEach(button=>button.addEventListener('click',()=>{selected=button.dataset.restaurantFilter;update();}));section.querySelector('[data-restaurant-reset]').addEventListener('click',()=>{input.value='';selected='all';update();input.focus();});
 section.querySelector('[data-restaurant-tools]').hidden=false;update();
})();

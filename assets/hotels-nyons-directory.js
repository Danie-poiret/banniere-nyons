(() => {
  const root=document.querySelector('[data-hotel-directory]');
  if(!root)return;
  const body=root.querySelector('tbody');
  const rows=Array.from(body.querySelectorAll('tr'));
  const stars=root.querySelector('#hotel-stars');
  const pool=root.querySelector('#hotel-pool');
  const closure=root.querySelector('#hotel-closures');
  const sort=root.querySelector('#hotel-sort');
  const count=root.querySelector('[data-hotel-count]');
  const empty=root.querySelector('[data-hotel-empty]');
  root.querySelector('[data-hotel-filters]').hidden=false;
  root.querySelector('[data-hotel-reset]').addEventListener('click',()=>{stars.value='all';pool.checked=false;closure.checked=false;sort.value='distance';update();});
  const update=()=>{
    const ordered=rows.slice().sort((a,b)=>{
      if(sort.value==='stars')return Number(b.dataset.stars)-Number(a.dataset.stars)||Number(a.dataset.distance)-Number(b.dataset.distance);
      if(sort.value==='name')return a.dataset.name.localeCompare(b.dataset.name,'fr');
      return Number(a.dataset.distance)-Number(b.dataset.distance)||a.dataset.name.localeCompare(b.dataset.name,'fr');
    });
    let shown=0;
    ordered.forEach(row=>{
      const visible=(stars.value==='all'||row.dataset.stars===stars.value)&&(!pool.checked||row.dataset.pool==='yes')&&(!closure.checked||row.dataset.closure!=='yes');
      row.hidden=!visible;
      if(visible)shown++;
      body.appendChild(row);
    });
    count.textContent=shown+' hôtel'+(shown>1?'s':'')+' affiché'+(shown>1?'s':'')+' sur '+rows.length;
    empty.hidden=shown!==0;
  };
  [stars,pool,closure,sort].forEach(control=>control.addEventListener('change',update));
  update();
})();
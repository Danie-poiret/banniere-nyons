/* Two shared partner cards below the heading, with La Lézardière first. */
(function installNyonsPartnerCards(){
  function install(){
    if(document.querySelector('[data-nyons-partner-cards]'))return;
    const slot=document.querySelector('[data-nyons-partner-slot]');
    const legacy=[...document.querySelectorAll('iframe[src*="/banniere-livres/"],img[src*="banniere-livres-drome-ardeche.png"]')].map(el=>el.closest('aside.top,.banner')||el.closest('a.ad-shell')||el).filter((el,index,all)=>all.indexOf(el)===index);
    const heading=document.querySelector('body > .hero,main .hero,main header');
    const anchor=heading||slot||legacy[0]||document.querySelector('body > .hero')||document.querySelector('main header,main .hero')||document.querySelector('main')||document.querySelector('header');if(!anchor)return;
    const canonical=document.querySelector('link[rel="canonical"]');
    const path=(canonical?new URL(canonical.href,location.href).pathname:location.pathname).toLowerCase();
    const omitLodging=path.includes('/la-lezardiere/')||path.includes('/demande-sejour-lezardiere/')||!!document.querySelector('[data-lezardiere-api]');
    const group=document.createElement('div');group.className='nyons-partner-cards';group.dataset.nyonsPartnerCards='';group.setAttribute('data-nosnippet','');
    const items=[];
    if(!omitLodging)items.push({key:'lezardiere',label:'La Lézardière, adresse partenaire à Nyons',photo:'https://www.vivreanyons.fr/assets/lezardiere/mini-villa.webp',alt:'La villa de La Lézardière et son jardin à Nyons',title:'☀️ UN SÉJOUR À NYONS ?',copy:'Papy Chris te recommande de découvrir La Lézardière !',href:'https://www.vivreanyons.fr/demande-sejour-lezardiere/',cta:'Demander les disponibilités →',note:'Adresse partenaire de Vivre à Nyons'});
    items.push({key:'livres',label:'Sélection de vieux livres sur Nyons',photo:'https://www.vivreanyons.fr/assets/nyons-livres-mini.webp',alt:'Livres sur Nyons dans le visuel de la sélection de Papy Chris',title:'📚 VIEUX LIVRES SUR NYONS',copy:'Histoire, souvenirs, cartes postales anciennes… Découvre la sélection de Papy Chris.',href:'https://amzn.to/3VzucHH',cta:'Voir ma sélection de livres →',note:'La sélection de Papy Chris sur Amazon.fr'});
    items.forEach(item=>{
      const card=document.createElement('aside');card.className='nyons-partner-card';card.dataset.nyonsPartner=item.key;card.setAttribute('aria-label',item.label);
      const photo=document.createElement('img');photo.src=item.photo;photo.alt=item.alt;photo.width=88;photo.height=88;photo.loading='lazy';photo.decoding='async';
      const copy=document.createElement('div');copy.className='nyons-partner-copy';const p=document.createElement('p');const title=document.createElement('strong');title.textContent=item.title;p.append(title,document.createTextNode(' '+item.copy));
      const link=document.createElement('a');link.href=item.href;link.textContent=item.cta;link.rel='sponsored';if(item.key==='livres'){link.target='_blank';link.rel+=' noopener noreferrer';}
      const note=document.createElement('span');note.textContent=item.note;copy.append(p,link,note);card.append(photo,copy);group.append(card);
    });
    const style=document.createElement('style');style.dataset.nyonsPartnerStyle='';
    style.textContent='body>.hero:has(+.nyons-partner-cards){margin-bottom:0!important}.nyons-partner-cards{box-sizing:border-box;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));grid-auto-rows:1fr;gap:18px;width:min(1120px,92%);margin:16px auto 0}main .nyons-partner-cards{width:100%;margin-bottom:24px}.nyons-partner-card{box-sizing:border-box;display:flex;align-items:center;gap:16px;min-width:0;min-height:150px;padding:18px;background:#f3f1e5;border:1px solid #dedecb;border-left:4px solid #768b5b;border-radius:12px;color:#344f38;font-family:system-ui,sans-serif}.nyons-partner-card>img{display:block;flex:0 0 88px;width:88px;height:88px;object-fit:cover;border-radius:9px}.nyons-partner-copy{min-width:0}.nyons-partner-copy p{margin:0 0 7px;font-size:14px;line-height:1.5}.nyons-partner-copy a{display:inline-block;color:#295646;font-size:14px;font-weight:750;text-decoration:underline;text-underline-offset:4px;padding:5px 0}.nyons-partner-copy a:focus-visible{outline:3px solid #668360;outline-offset:4px;border-radius:3px}.nyons-partner-copy span{display:block;margin-top:4px;font-size:11px;color:#63705d}@media(max-width:760px){.nyons-partner-cards{grid-template-columns:1fr;gap:14px}.nyons-partner-card{min-height:176px;padding:16px 14px;gap:14px}}';
    document.head.append(style);if(heading){heading.after(group);if(slot)slot.remove();}else if(slot){slot.replaceWith(group);}else if(legacy.length){anchor.before(group);}else if(anchor.tagName==='MAIN'){anchor.prepend(group);}else{anchor.after(group);}legacy.forEach(el=>el.remove());
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();

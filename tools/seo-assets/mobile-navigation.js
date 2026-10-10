/* Keep every existing navigation link; collapse the menu only on narrow screens. */
(function installNyonsMobileNavigation(){
  const nav=document.querySelector('header .nav');
  const menu=nav&&nav.querySelector('.navlinks');
  if(!nav||!menu||nav.querySelector('[data-mobile-menu-toggle]'))return;
  const button=document.createElement('button');
  button.type='button';button.className='nav-mobile-toggle';button.setAttribute('data-mobile-menu-toggle','');
  if(!menu.id)menu.id='nyons-main-menu';
  button.setAttribute('aria-controls',menu.id);button.setAttribute('aria-expanded','false');
  button.textContent='Menu';nav.insertBefore(button,menu);
  nav.setAttribute('data-mobile-ready','true');
  const narrow=window.matchMedia('(max-width:800px)');let open=false;
  function display(){
    button.hidden=!narrow.matches;
    menu.hidden=narrow.matches&&!open;
    button.setAttribute('aria-expanded',String(narrow.matches&&open));
    button.textContent=open&&narrow.matches?'Fermer le menu':'Menu';
  }
  button.addEventListener('click',()=>{open=!open;display();});
  nav.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&narrow.matches&&open){open=false;display();button.focus();}
  });
  menu.addEventListener('click',event=>{if(narrow.matches&&event.target.closest('a')){open=false;display();}});
  document.addEventListener('click',event=>{if(narrow.matches&&open&&!nav.contains(event.target)){open=false;display();}});
  function resize(){open=narrow.matches&&menu.contains(document.activeElement);display();}
  if(narrow.addEventListener)narrow.addEventListener('change',resize);else narrow.addListener(resize);
  display();
})();

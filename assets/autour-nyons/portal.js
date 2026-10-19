(() => {
  'use strict';
  const form = document.getElementById('autour-filters');
  if (!form) return;
  const cards = [...document.querySelectorAll('[data-autour-card]')];
  const groups = [...document.querySelectorAll('[data-autour-group]')];
  const search = document.getElementById('autour-search');
  const category = document.getElementById('autour-category');
  const season = document.getElementById('autour-season');
  const count = document.getElementById('autour-count');
  const empty = document.getElementById('autour-empty');
  const norm = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr');
  cards.forEach(card => { card.searchText = norm(card.dataset.search); });
  function filter() {
    const words = norm(search.value).trim().split(/\s+/).filter(Boolean);
    let found = 0;
    cards.forEach(card => {
      const visible = words.every(word => card.searchText.includes(word)) && (!category.value || card.dataset.group === category.value) && (!season.value || card.dataset.seasons.split(' ').includes(season.value));
      card.hidden = !visible;
      if (visible) found++;
    });
    groups.forEach(group => { group.hidden = ![...group.querySelectorAll('[data-autour-card]')].some(card => !card.hidden); });
    count.textContent = found + (found > 1 ? ' idées de sorties' : ' idée de sortie');
    empty.hidden = found > 0;
  }
  form.hidden = false;
  form.addEventListener('submit', event => event.preventDefault());
  [search, category, season].forEach(input => input.addEventListener('input', filter));
  form.addEventListener('reset', () => { search.value = ''; category.value = ''; season.value = ''; filter(); });
  filter();
})();

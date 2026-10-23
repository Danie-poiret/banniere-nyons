/* Progressive enhancement of the initial HTML catalogue; no API or remote AI. */
(function () {
  'use strict';
  const root = document.querySelector('[data-activity-search]');
  if (!root) return;
  const form = root.querySelector('form'), input = root.querySelector('[type="search"]');
  const category = root.querySelector('#activity-category'), zone = root.querySelector('#activity-zone');
  const checks = [...root.querySelectorAll('[name="facet"]')];
  const details = root.querySelector('#activity-results'), summary = details.querySelector('summary');
  const status = root.querySelector('[role="status"]'), empty = root.querySelector('[data-activity-empty]');
  const more = root.querySelector('[data-activity-more]'), display = root.querySelector('[data-activity-display]');
  const list = root.querySelector('[data-activity-list]');
  const normalize = text => text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/œ/g, 'oe');
  const groups = [
    ['randonnee','randonnees','rando','randos','hiking'],
    ['balade','balades','promenade','promenades'], ['marcher','walking','pied','pieds'],
    ['famille','familial','familiale','familles','enfants','enfant','kids'],
    ['cinema','cine','film','films'], ['petanque','boules','boule','boulodrome','cochonnet'],
    ['velo','velos','cyclisme','vtt','bike'], ['courir','running','jogging','footing'],
    ['eglise','eglises'], ['musee','musees'],
    ['piscine','piscines','nager','natation','baignade','aquatique'],
    ['theatre','theatres'], ['gratuit','gratuite','gratuits','gratuites','gratuitement'],
    ['pluie','pleut','pluvieux','abri','interieur'], ['senior','seniors','seniore','seniors'],
    ['olive','olives','olivier','oliviers','oliveraie','oliveraies'], ['facile','faciles']
  ];
  const aliases = new Map(); groups.forEach(group => group.forEach(word => aliases.set(word, group[0])));
  const ignored = new Set(['a','au','aux','avec','d','de','des','du','en','et','l','la','le','les','un','une','pour','que','faire','activite','activites','nyons','quand','il']);
  const words = text => (normalize(text).match(/[a-z0-9]+/g) || []).filter(word => !ignored.has(word)).map(word => aliases.get(word) || word);
  const entries = [...root.querySelectorAll('[data-activity]')].map((node, order) => ({
    node, order, words: words(node.querySelector('h3').textContent + ' ' + node.querySelector('p').textContent + ' ' + node.dataset.keywords + ' ' + node.dataset.categories),
    title: words(node.querySelector('a').textContent), categories: node.dataset.categories.split(' '),
    facets: node.dataset.facets.split(' '), zone: node.dataset.zone
  }));
  const special = new Map([['gratuit','gratuit'],['pluie','pluie'],['famille','famille'],['senior','senior'],['marcher','marche']]);
  const matches = (terms, term) => terms.some(word => word === term || (term.length >= 4 && word.startsWith(term)));
  let limit = 8;
  function update(resetLimit = true) {
    if (resetLimit) limit = 8;
    const query = words(input.value), terms = query.filter(term => !special.has(term));
    const facets = [...checks.filter(check => check.checked).map(check => check.value), ...query.filter(term => special.has(term)).map(term => special.get(term))];
    const results = entries.filter(entry =>
      (!category.value || entry.categories.includes(category.value)) && (!zone.value || entry.zone === zone.value) &&
      facets.every(facet => entry.facets.includes(facet)) && terms.every(term => matches(entry.words, term))
    ).map(entry => ({...entry, score: terms.reduce((score, term) => score + (matches(entry.title, term) ? 1 : 0), 0)}))
      .sort((a,b) => (a.zone === 'autour') - (b.zone === 'autour') || b.score - a.score || a.order - b.order);
    entries.forEach(entry => {entry.node.hidden = true;});
    results.forEach((entry, i) => {entry.node.hidden = i >= limit; list.appendChild(entry.node);});
    const count = results.length, shown = Math.min(count,limit);
    status.textContent = count + (count === 1 ? ' activité trouvée' : ' activités trouvées');
    summary.textContent = 'Résultats (' + count + ')';
    display.textContent = shown + ' sur ' + count + (count === 1 ? ' activité affichée' : ' activités affichées');
    display.hidden = count === 0; empty.hidden = count !== 0; more.hidden = count <= limit;
    more.textContent = 'Afficher ' + Math.min(8,count-shown) + ' activités de plus';
    details.open = true;
  }
  input.addEventListener('input', () => update());
  form.addEventListener('change', () => update());
  form.addEventListener('submit', event => {event.preventDefault(); update();});
  form.addEventListener('reset', event => {
    event.preventDefault(); input.value = ''; category.value = ''; zone.value = '';
    checks.forEach(check => {check.checked = false;}); update(); input.focus();
  });
  more.addEventListener('click', () => {
    const previous = [...list.querySelectorAll('[data-activity]:not([hidden])')].length;
    limit += 8; update(false);
    const next = list.querySelectorAll('[data-activity]:not([hidden])')[previous];
    if (next) next.querySelector('a').focus();
  });
  root.querySelectorAll('[data-activity-query]').forEach(button => button.addEventListener('click', () => {
    input.value = button.dataset.activityQuery; update(); input.focus();
  }));
  form.hidden = false; root.querySelector('[data-activity-shortcuts]').hidden = false; status.hidden = false;
  update();
})();

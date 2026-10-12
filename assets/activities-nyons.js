/* The searchable index is the existing HTML list: no API, storage or network request. */
(function () {
  'use strict';
  const root = document.querySelector('[data-activity-search]');
  if (!root) return;
  const form = root.querySelector('form');
  const input = root.querySelector('[type="search"]');
  const category = root.querySelector('select');
  const details = root.querySelector('details');
  const summary = details.querySelector('summary');
  const status = root.querySelector('[role="status"]');
  const empty = root.querySelector('[data-activity-empty]');
  const normalize = text => text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/œ/g, 'oe');
  const groups = [
    ['randonnee', 'randonnees', 'rando', 'randos', 'hiking'],
    ['balade', 'balades', 'promenade', 'promenades'],
    ['enfant', 'enfants', 'famille', 'familles', 'familial', 'familiale', 'kids'],
    ['cinema', 'cine', 'film', 'films'],
    ['petanque', 'boules', 'boulodrome', 'cochonnet'],
    ['padel', 'paddle'],
    ['velo', 'velos', 'cyclisme', 'vtt', 'bike'],
    ['courir', 'running', 'jogging', 'footing'],
    ['eglise', 'eglises'],
    ['musee', 'musees'],
    ['piscine', 'piscines', 'nager', 'natation', 'baignade'],
    ['theatre', 'theatres'],
    ['gratuit', 'gratuite', 'gratuits', 'gratuites'],
    ['facile', 'faciles'],
    ['concert', 'concerts'], ['spectacle', 'spectacles'], ['fete', 'fetes']
  ];
  const aliases = new Map();
  groups.forEach(group => group.forEach(word => aliases.set(word, group[0])));
  const ignored = new Set(['a', 'au', 'aux', 'avec', 'd', 'de', 'des', 'du', 'en', 'et', 'l', 'la', 'le', 'les', 'un', 'une', 'pour', 'que', 'faire', 'activite', 'activites', 'nyons']);
  const words = text => (normalize(text).match(/[a-z0-9]+/g) || []).filter(word => !ignored.has(word)).map(word => aliases.get(word) || word);
  const entries = Array.from(root.querySelectorAll('[data-activity]')).map((node, order) => ({
    node, order,
    words: words(node.textContent + ' ' + node.dataset.keywords),
    title: words(node.querySelector('a').textContent),
    categories: node.dataset.categories.split(' ')
  }));
  const matchesWord = (list, term) => list.some(word => word === term || (term.length >= 4 && word.startsWith(term)));
  function update() {
    const terms = words(input.value);
    const filtered = input.value.trim() !== '' || category.value !== '';
    const ranked = entries.map(entry => ({
      ...entry,
      visible: (!category.value || entry.categories.includes(category.value)) && terms.every(term => matchesWord(entry.words, term)),
      score: terms.reduce((score, term) => score + (matchesWord(entry.title, term) ? 1 : 0), 0)
    })).sort((a, b) => b.score - a.score || a.order - b.order);
    const list = root.querySelector('[data-activity-list]');
    ranked.forEach(entry => { entry.node.hidden = !entry.visible; list.appendChild(entry.node); });
    const count = ranked.filter(entry => entry.visible).length;
    status.textContent = count + (count === 1 ? ' activité trouvée' : ' activités trouvées');
    summary.textContent = filtered ? 'Résultats de la recherche (' + count + ')' : 'Parcourir les ' + entries.length + ' activités';
    empty.hidden = count !== 0;
    details.open = filtered;
  }
  input.addEventListener('input', update);
  category.addEventListener('change', update);
  form.addEventListener('submit', event => { event.preventDefault(); update(); });
  form.addEventListener('reset', event => {
    event.preventDefault(); input.value = ''; category.value = ''; update(); input.focus();
  });
  root.querySelectorAll('[data-activity-query]').forEach(button => button.addEventListener('click', () => {
    input.value = button.dataset.activityQuery; category.value = ''; update(); input.focus();
  }));
  form.hidden = false;
  root.querySelector('[data-activity-shortcuts]').hidden = false;
  status.hidden = false;
  update();
})();

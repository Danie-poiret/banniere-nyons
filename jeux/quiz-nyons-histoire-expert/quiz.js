/* One local game. No account, storage, server call or automatic publication. */
(function () {
  'use strict';
  const QUESTIONS = [{"id":1,"category":"Les vieilles pierres et leurs secrets","question":"Que représentent réellement les trois têtes couronnées de la fontaine des Trois Rois ?","options":["Trois rois mages","Trois lions","Trois dragons","Trois chevaliers"],"correct":1,"explanation":"L'imagination populaire y a vu les rois mages, mais la pierre armoriée représente trois têtes de lions couronnées. Un joli piège pour les connaisseurs !","issue":11,"year":1993,"page":33,"pdfPage":35,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1993_11.pdf#page=35","sourceLabel":"Terre d’Eygues n° 11 (1993), page imprimée 33 · Consulter le PDF ↗"},{"id":2,"category":"Les vieilles pierres et leurs secrets","question":"À quel personnage sont attribuées les armoiries de cette fontaine ?","options":["Paul Vigne","Augustin Fresnel","Jean de Beins","Louis-Gabriel d'Urre-Brotin"],"correct":3,"explanation":"La sculpture porte les armes du marquis de Bressieux, mort en 1700 sans postérité. L'origine exacte de la pierre reste incertaine.","issue":11,"year":1993,"page":33,"pdfPage":35,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1993_11.pdf#page=35","sourceLabel":"Terre d’Eygues n° 11 (1993), page imprimée 33 · Consulter le PDF ↗"},{"id":3,"category":"Les vieilles pierres et leurs secrets","question":"Quelle rue actuelle portait autrefois le nom de « rue Sournure » ?","options":["Rue des Grands Forts","Rue des Déportés","Rue de la Résistance","Rue des Petits Forts"],"correct":0,"explanation":"Cette ancienne rue fortifiée protégeait l'ouest de la ville. Elle était percée d'archères.","issue":8,"year":1991,"page":3,"pdfPage":7,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1991_08.pdf#page=7","sourceLabel":"Terre d’Eygues n° 8 (1991), page imprimée 3 · Consulter le PDF ↗"},{"id":4,"category":"Les vieilles pierres et leurs secrets","question":"Quel était l'ancien nom de la rue des Petits Forts ?","options":["Rue du Moulin","Rue du Foussat","Rue du Devès","Rue des Halles"],"correct":2,"explanation":"Cette rue abritait notamment la châtellenie, l'hôtel de ville et divers services administratifs dans la cité médiévale.","issue":8,"year":1991,"page":3,"pdfPage":7,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1991_08.pdf#page=7","sourceLabel":"Terre d’Eygues n° 8 (1991), page imprimée 3 · Consulter le PDF ↗"},{"id":5,"category":"Les vieilles pierres et leurs secrets","question":"Avant la construction du Pont Roman, comment franchissait-on l'Eygues ?","options":["Avec une barque à péage","Par un pont suspendu en bois","Par un passage souterrain","Avec un bac gratuit à chevaux"],"correct":0,"explanation":"Avant le pont médiéval, une barque payante reliait le port de Nyons au secteur de l'actuelle route des Rieux.","issue":12,"year":1993,"page":7,"pdfPage":11,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1993_12.pdf#page=11","sourceLabel":"Terre d’Eygues n° 12 (1993), page imprimée 7 · Consulter le PDF ↗"},{"id":6,"category":"Une ville vieille de plusieurs siècles","question":"Comment se nommait le premier noyau de Nyons vers l'an 1200 ?","options":["Le Bourg Saint-Césaire","La Grande Prairie","Les Bas-Bourgs","Le Castrum Nyonis"],"correct":3,"explanation":"Ce premier noyau urbain s'est développé sur les pentes de la montagne de Vaux.","issue":12,"year":1993,"page":6,"pdfPage":10,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1993_12.pdf#page=10","sourceLabel":"Terre d’Eygues n° 12 (1993), page imprimée 6 · Consulter le PDF ↗"},{"id":7,"category":"Une ville vieille de plusieurs siècles","question":"Vers quelle époque le quartier des Halles s'est-il ajouté à la ville haute ?","options":["Vers 1100","Vers 1350","Vers 1600","Vers 1750"],"correct":1,"explanation":"Le quartier des Halles constitue une étape importante de l'extension de la ville basse, entre la cité primitive et l'Eygues.","issue":12,"year":1993,"page":6,"pdfPage":10,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1993_12.pdf#page=10","sourceLabel":"Terre d’Eygues n° 12 (1993), page imprimée 6 · Consulter le PDF ↗"},{"id":8,"category":"Une ville vieille de plusieurs siècles","question":"Quelle communauté participa à la construction des Bas-Bourgs au début du XVe siècle ?","options":["Des marchands génois","Des chevaliers hospitaliers","La communauté juive","Des moines bénédictins"],"correct":2,"explanation":"L'étude d'histoire urbaine attribue la construction de ce quartier à la communauté juive. Celle-ci dut ensuite quitter la ville sous les persécutions.","issue":12,"year":1993,"page":6,"pdfPage":10,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1993_12.pdf#page=10","sourceLabel":"Terre d’Eygues n° 12 (1993), page imprimée 6 · Consulter le PDF ↗"},{"id":9,"category":"Une ville vieille de plusieurs siècles","question":"Quel bâtiment accueillit l'hôtel de ville place Saint-Césaire pendant environ 185 ans ?","options":["Un ancien couvent","Une ancienne caserne","Un ancien moulin","Une ancienne auberge"],"correct":0,"explanation":"L'hôtel de ville occupa les anciens locaux d'un couvent de religieuses avant son transfert de 1991.","issue":8,"year":1991,"page":2,"pdfPage":6,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1991_08.pdf#page=6","sourceLabel":"Terre d’Eygues n° 8 (1991), page imprimée 2 · Consulter le PDF ↗"},{"id":10,"category":"Une ville vieille de plusieurs siècles","question":"Quelle était la fonction précédente du bâtiment devenu mairie en 1991 ?","options":["Un tribunal","Une manufacture de soie","Un hôpital","Une gendarmerie"],"correct":3,"explanation":"La nouvelle mairie a été installée dans les bâtiments restaurés et transformés de l'ancienne gendarmerie.","issue":8,"year":1991,"page":2,"pdfPage":6,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1991_08.pdf#page=6","sourceLabel":"Terre d’Eygues n° 8 (1991), page imprimée 2 · Consulter le PDF ↗"},{"id":11,"category":"Le marché que nos anciens ont connu","question":"Quel personnage accorda aux Nyonsais une charte évoquant les marchés en 1337 ?","options":["Louis XI","François Ier","Humbert II, dauphin du Viennois","Henri IV"],"correct":2,"explanation":"Une charte du 6 juin 1337 contient déjà des dispositions concernant les jours de foire et de marché.","issue":1,"year":1987,"page":2,"pdfPage":6,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1987_01.pdf#page=6","sourceLabel":"Terre d’Eygues n° 1 (1987), page imprimée 2 · Consulter le PDF ↗"},{"id":12,"category":"Le marché que nos anciens ont connu","question":"Quel roi autorisa un marché le jeudi par une lettre de 1541 ?","options":["Charles VIII","François Ier","Henri II","Louis XII"],"correct":1,"explanation":"La revue mentionne une lettre patente du 29 juillet 1541 relative à la création du marché du jeudi.","issue":1,"year":1987,"page":2,"pdfPage":6,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1987_01.pdf#page=6","sourceLabel":"Terre d’Eygues n° 1 (1987), page imprimée 2 · Consulter le PDF ↗"},{"id":13,"category":"Le marché que nos anciens ont connu","question":"D'après l'enquête sur le marché menée en 1986, de combien de départements voisins venaient les marchands forains ?","options":["Sept","Trois","Dix","Douze"],"correct":0,"explanation":"L'attraction du marché dépassait largement Nyons. Certains marchands parcouraient plus de 100 kilomètres pour venir vendre.","issue":2,"year":1988,"page":2,"pdfPage":6,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1988_02.pdf#page=6","sourceLabel":"Terre d’Eygues n° 2 (1988), page imprimée 2 · Consulter le PDF ↗"},{"id":14,"category":"Le marché que nos anciens ont connu","question":"Dans le marché décrit en 1986, quelle place accueillait principalement les fleurs ?","options":["Place Saint-Césaire","Place des Arcades","Place du Foussat","Place du Docteur Bourdongle"],"correct":3,"explanation":"La partie nord de cette place était particulièrement consacrée au marché aux fleurs.","issue":1,"year":1987,"page":6,"pdfPage":10,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1987_01.pdf#page=10","sourceLabel":"Terre d’Eygues n° 1 (1987), page imprimée 6 · Consulter le PDF ↗"},{"id":15,"category":"Le marché que nos anciens ont connu","question":"Quelle rue accueillait une trentaine d'artisans les jours de marché en 1986 ?","options":["Rue des Déportés","Rue Pierre-Toesca","Rue de la Résistance","Rue des Petits Forts"],"correct":2,"explanation":"Bijoux, jouets, cuir et tissus faisaient partie des activités évoquées dans cette rue très animée.","issue":1,"year":1987,"page":6,"pdfPage":10,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1987_01.pdf#page=10","sourceLabel":"Terre d’Eygues n° 1 (1987), page imprimée 6 · Consulter le PDF ↗"},{"id":16,"category":"Les moulins, l'huile et la soie","question":"Quel seigneur provoqua un conflit en 1488 après avoir détourné l'eau du canal pour son moulin à huile ?","options":["Jean de Beins","Fernand Dies","Louis-Gabriel d'Urre","Jacques Martin Dédier"],"correct":1,"explanation":"Les habitants protestèrent parce qu'ils avaient besoin de cette eau pour leurs activités et leurs terres.","issue":5,"year":1990,"page":18,"pdfPage":22,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1990_05.pdf#page=22","sourceLabel":"Terre d’Eygues n° 5 (1990), page imprimée 18 · Consulter le PDF ↗"},{"id":17,"category":"Les moulins, l'huile et la soie","question":"Quel obstacle foncier fallut-il surmonter pour aménager le canal au début du XVIIIe siècle ?","options":["Traverser le cimetière communal","Acheter un château royal","Déplacer la place du marché","Passer dans une propriété appartenant à des religieuses"],"correct":3,"explanation":"Le Parlement autorisa le passage en 1704. Les travaux furent confiés à des entrepreneurs en 1707.","issue":5,"year":1990,"page":17,"pdfPage":21,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1990_05.pdf#page=21","sourceLabel":"Terre d’Eygues n° 5 (1990), page imprimée 17 · Consulter le PDF ↗"},{"id":18,"category":"Les moulins, l'huile et la soie","question":"Combien de moulins à huile comptait Nyons en 1826 ?","options":["Treize","Cinq","Vingt-sept","Quarante"],"correct":0,"explanation":"Cette activité était alors importante dans l'économie locale. Neuf de ces moulins avaient disparu entre 1826 et 1872.","issue":5,"year":1990,"page":31,"pdfPage":35,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1990_05.pdf#page=35","sourceLabel":"Terre d’Eygues n° 5 (1990), page imprimée 31 · Consulter le PDF ↗"},{"id":19,"category":"Les moulins, l'huile et la soie","question":"Combien d'ouvriers travaillaient dans les six fabriques de soie de Nyons en 1826, selon les données historiques reprises dans la revue ?","options":["75","140","280","620"],"correct":2,"explanation":"Le travail de la soie représentait une activité industrielle majeure à Nyons, bien avant son économie principalement touristique.","issue":1,"year":1987,"page":2,"pdfPage":6,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1987_01.pdf#page=6","sourceLabel":"Terre d’Eygues n° 1 (1987), page imprimée 2 · Consulter le PDF ↗"},{"id":20,"category":"Les moulins, l'huile et la soie","question":"Combien fallait-il environ de kilos de noix entières pour produire un litre d'huile de noix ?","options":["Deux kilos","Cinq kilos","Dix kilos","Quinze kilos"],"correct":1,"explanation":"L'étude évoque cinq kilos de noix ou deux kilos de cerneaux. Rien ne se perdait : même les résidus du pressage étaient utilisés.","issue":9,"year":1992,"page":39,"pdfPage":43,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1992_09.pdf#page=43","sourceLabel":"Terre d’Eygues n° 9 (1992), page imprimée 39 · Consulter le PDF ↗"},{"id":21,"category":"Les métiers et la vie quotidienne disparus","question":"Que faisait-on dans une magnanerie ?","options":["On fabriquait des chandelles","On entreposait les olives","On tissait des paniers","On élevait des vers à soie"],"correct":3,"explanation":"L'élevage des magnans constituait une étape fondamentale de la production de la soie.","issue":6,"year":1991,"page":9,"pdfPage":13,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1991_06.pdf#page=13","sourceLabel":"Terre d’Eygues n° 6 (1991), page imprimée 9 · Consulter le PDF ↗"},{"id":22,"category":"Les métiers et la vie quotidienne disparus","question":"Selon l'étude historique, quelle quantité de feuilles de mûrier fallait-il environ pendant 32 jours pour nourrir les vers issus d'une once de graines ?","options":["1 200 kilos","120 kilos","400 kilos","3 000 kilos"],"correct":0,"explanation":"La consommation augmentait énormément vers la fin de l'élevage. Les dix derniers jours demandaient à eux seuls environ 950 kilos de feuilles.","issue":6,"year":1991,"page":11,"pdfPage":15,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1991_06.pdf#page=15","sourceLabel":"Terre d’Eygues n° 6 (1991), page imprimée 11 · Consulter le PDF ↗"},{"id":23,"category":"Les métiers et la vie quotidienne disparus","question":"Comment Ferdinand Brunel, épicier livreur du Planteur du Caïffa, effectuait-il ses premières tournées en 1911 ?","options":["En automobile","À bicyclette avec remorque","À pied, en poussant un triporteur","En charrette tirée par un âne"],"correct":2,"explanation":"Il parcourait les chemins non goudronnés et allait de ferme en ferme pour vendre notamment du café.","issue":11,"year":1993,"page":27,"pdfPage":29,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1993_11.pdf#page=29","sourceLabel":"Terre d’Eygues n° 11 (1993), page imprimée 27 · Consulter le PDF ↗"},{"id":24,"category":"Les métiers et la vie quotidienne disparus","question":"Combien de clients Ferdinand Brunel devait-il visiter du lundi au samedi selon son contrat de 1919 ?","options":["120","308","500","75"],"correct":1,"explanation":"Son itinéraire hebdomadaire couvrait Nyons et plusieurs villages voisins. Les déplacements pouvaient être particulièrement pénibles.","issue":11,"year":1993,"page":29,"pdfPage":31,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1993_11.pdf#page=31","sourceLabel":"Terre d’Eygues n° 11 (1993), page imprimée 29 · Consulter le PDF ↗"},{"id":25,"category":"Les métiers et la vie quotidienne disparus","question":"Vers 1927-1928, quel équipement permit à cette famille d'épicier de faciliter les tournées ?","options":["Une camionnette électrique","Un side-car","Un tracteur","Un cheval et une jardinière"],"correct":3,"explanation":"La caisse de marchandises était désormais transportée sur une voiture légère à cheval pour les tournées en campagne, mais restait poussée à la main pour les livraisons en ville.","issue":11,"year":1993,"page":30,"pdfPage":32,"source":"https://terre-eygues.net/wp/wp-content/uploads/2017/06/TE1993_11.pdf#page=32","sourceLabel":"Terre d’Eygues n° 11 (1993), page imprimée 30 · Consulter le PDF ↗"}];
  const QUIZ_URL = 'https://www.vivreanyons.fr/jeux/quiz-nyons-histoire-expert/';
  function messageFor(score) {
    if (!Number.isInteger(score) || score < 0 || score > 25) throw new RangeError('Score invalide');
    if (score <= 5) return 'Les archives ont encore de belles surprises à te réserver !';
    if (score <= 10) return 'Tu découvres déjà les secrets du Nyons d’autrefois !';
    if (score <= 15) return 'Bien joué ! Tu as de solides repères dans l’histoire de Nyons.';
    if (score <= 20) return 'Bravo ! Tu connais très bien le passé de notre ville.';
    if (score <= 24) return "Impressionnant ! Tu as une vraie mémoire du Nyons d’autrefois.";
    return '25 sur 25 ! Le défi historique des anciens est relevé !';
  }
  function shareText(score) {
    messageFor(score);
    return "🏆 J'ai obtenu " + score + '/25 au quiz CONNAIS-TU LE NYONS D’AUTREFOIS ? — NIVEAU EXPERT Et toi, feras-tu mieux que moi ? 👉 ' + QUIZ_URL;
  }
  function facebookUrl() { return 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(QUIZ_URL); }
  class QuizGame {
    constructor() { this.reset(); }
    reset() { this.index = 0; this.score = 0; this.locked = false; this.finished = false; }
    answer(choice) {
      if (this.locked || this.finished || !Number.isInteger(choice) || choice < 0 || choice > 3) return null;
      const question = QUESTIONS[this.index];
      const correct = choice === question.correct;
      this.locked = true;
      if (correct) this.score += 1;
      return { correct, question, choice };
    }
    next() {
      if (!this.locked || this.finished) return false;
      if (this.index === QUESTIONS.length - 1) { this.finished = true; return true; }
      this.index += 1; this.locked = false; return true;
    }
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { QUESTIONS, QuizGame, messageFor, shareText, facebookUrl, QUIZ_URL };
  }
  if (typeof document === 'undefined') return;
  const game = new QuizGame();
  const byId = id => document.getElementById(id);
  const form = byId('quiz-form');
  const options = byId('quiz-options');
  const validate = byId('quiz-validate');
  const feedback = byId('quiz-feedback');
  const next = byId('quiz-next');
  const result = byId('quiz-result');
  let cardObjectUrl = null;
  let cardGeneration = 0;
  const letters = ['A', 'B', 'C', 'D'];
  function renderQuestion(focus) {
    const question = QUESTIONS[game.index];
    byId('quiz-position').textContent = 'Question ' + (game.index + 1) + ' sur 25';
    byId('quiz-progress').value = game.index;
    byId('quiz-current-score').textContent = game.score + ' / 25';
    byId('quiz-theme').textContent = question.category;
    byId('quiz-question').textContent = question.question;
    options.replaceChildren();
    question.options.forEach((answer, index) => {
      const label = document.createElement('label'); label.className = 'quiz-choice';
      const radio = document.createElement('input'); radio.type = 'radio'; radio.name = 'answer'; radio.value = String(index);
      const letter = document.createElement('span'); letter.className = 'quiz-letter'; letter.textContent = letters[index]; letter.setAttribute('aria-hidden', 'true');
      const text = document.createElement('span'); text.className = 'quiz-choice-text'; text.textContent = answer;
      label.append(radio, letter, text); options.append(label);
    });
    validate.disabled = true; validate.hidden = false; feedback.hidden = true; next.hidden = true;
    byId('quiz-answer-hint').textContent = 'Choisis une réponse, puis valide.';
    if (focus) byId('quiz-question').focus();
  }
  options.addEventListener('change', () => { if (!game.locked) validate.disabled = !form.querySelector('input[name="answer"]:checked'); });
  form.addEventListener('submit', event => {
    event.preventDefault();
    const selected = form.querySelector('input[name="answer"]:checked');
    if (!selected) return;
    const answer = game.answer(Number(selected.value));
    if (!answer) return;
    options.querySelectorAll('input').forEach((input, index) => {
      input.disabled = true;
      if (index === answer.question.correct) input.closest('label').classList.add('is-correct');
      else if (index === answer.choice) input.closest('label').classList.add('is-incorrect');
    });
    validate.disabled = true; validate.hidden = true;
    byId('quiz-feedback-title').textContent = answer.correct ? '✓ Bonne réponse !' : 'La bonne réponse était ailleurs…';
    byId('quiz-correct-answer').textContent = 'Bonne réponse : ' + answer.question.options[answer.question.correct] + '.';
    byId('quiz-explanation').textContent = answer.question.explanation;
    byId('quiz-answer-source').href = answer.question.source;
    byId('quiz-answer-source').textContent = answer.question.sourceLabel;
    byId('quiz-current-score').textContent = game.score + ' / 25';
    byId('quiz-answer-hint').textContent = 'Réponse enregistrée. Un seul choix est comptabilisé.';
    feedback.classList.toggle('is-wrong', !answer.correct); feedback.hidden = false;
    next.textContent = game.index === 24 ? 'Voir mon résultat →' : 'Question suivante →'; next.hidden = false;
    byId('quiz-progress').value = game.index + 1;
    feedback.focus();
  });
  next.addEventListener('click', () => {
    if (!game.next()) return;
    if (game.finished) showResult(); else renderQuestion(true);
  });
  function showResult() {
    byId('quiz-game').hidden = true; result.hidden = false;
    byId('quiz-final-score').textContent = String(game.score);
    byId('quiz-result-message').textContent = messageFor(game.score);
    byId('quiz-facebook').href = facebookUrl();
    byId('quiz-share-status').textContent = '';
    byId('quiz-copy-fallback').hidden = true;
    byId('quiz-result-title').focus();
    makeCard(game.score);
  }
  byId('quiz-replay').addEventListener('click', () => {
    cardGeneration += 1;
    if (cardObjectUrl) { URL.revokeObjectURL(cardObjectUrl); cardObjectUrl = null; }
    byId('quiz-card-area').hidden = true; byId('quiz-download').hidden = true;
    byId('quiz-card-preview').removeAttribute('src');
    game.reset(); result.hidden = true; byId('quiz-game').hidden = false;
    renderQuestion(true);
  });
  byId('quiz-copy').addEventListener('click', async () => {
    const value = shareText(game.score);
    const status = byId('quiz-share-status');
    try {
      if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard non disponible');
      await navigator.clipboard.writeText(value);
      byId('quiz-copy-fallback').hidden = true;
      status.textContent = '✓ Ton score est copié. Ouvre Facebook et colle-le dans ta publication.';
    } catch (_) {
      const field = byId('quiz-copy-text');
      byId('quiz-copy-fallback').hidden = false; field.value = value; field.focus(); field.select(); field.setSelectionRange(0, value.length);
      let copied = false;
      try { copied = document.execCommand('copy'); } catch (_) { /* Manual selection remains available. */ }
      status.textContent = copied ? '✓ Ton score est copié. Tu peux le coller dans Facebook.' : 'Le texte est sélectionné : copie-le avec Ctrl+C, ou un appui long sur téléphone, puis colle-le dans Facebook.';
    }
  });
  function rounded(ctx, x, y, width, height, radius) {
    ctx.beginPath(); ctx.moveTo(x + radius, y); ctx.lineTo(x + width - radius, y); ctx.quadraticCurveTo(x + width, y, x + width, y + radius); ctx.lineTo(x + width, y + height - radius); ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height); ctx.lineTo(x + radius, y + height); ctx.quadraticCurveTo(x, y + height, x, y + height - radius); ctx.lineTo(x, y + radius); ctx.quadraticCurveTo(x, y, x + radius, y); ctx.closePath();
  }
  function wrapText(ctx, text, width, x, y, lineHeight) {
    let line = '';
    for (const word of text.split(' ')) {
      const candidate = line ? line + ' ' + word : word;
      if (line && ctx.measureText(candidate).width > width) { ctx.fillText(line, x, y); y += lineHeight; line = word; }
      else line = candidate;
    }
    if (line) ctx.fillText(line, x, y);
  }
  async function makeCard(score) {
    const generation = ++cardGeneration;
    const canvas = byId('quiz-result-canvas'); const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = '#f7f1df'; ctx.fillRect(0, 0, 1080, 1080);
    ctx.strokeStyle = '#6b7a4c'; ctx.lineWidth = 3; rounded(ctx, 27, 27, 1026, 1026, 26); ctx.stroke();
    ctx.textAlign = 'center'; ctx.fillStyle = '#52643c'; ctx.font = 'bold 24px Arial'; ctx.fillText('VIVRE À NYONS · DÉFI EXPERT DE PAPY CHRIS', 540, 91);
    ctx.fillStyle = '#253c31'; ctx.font = 'bold 48px Georgia'; ctx.fillText('CONNAIS-TU', 540, 175); ctx.fillText('LE NYONS D’AUTREFOIS ?', 540, 241);
    ctx.font = 'bold 23px Arial'; ctx.fillStyle = '#6b7658'; ctx.fillText('TON SCORE', 540, 307);
    ctx.font = 'bold 160px Georgia'; ctx.fillStyle = '#253c31'; ctx.fillText(score + ' / 25', 540, 464);
    const photo = byId('quiz-hero-photo');
    try {
      if (!photo.complete) await photo.decode();
      if (photo.naturalWidth) {
        ctx.save(); rounded(ctx, 66, 517, 948, 295, 20); ctx.clip();
        const targetRatio = 948 / 295; let sw = photo.naturalWidth; let sh = sw / targetRatio;
        if (sh > photo.naturalHeight) { sh = photo.naturalHeight; sw = sh * targetRatio; }
        ctx.drawImage(photo, (photo.naturalWidth - sw) / 2, (photo.naturalHeight - sh) / 2, sw, sh, 66, 517, 948, 295); ctx.restore();
      }
    } catch (_) { /* A text card still works if the photograph cannot load. */ }
    ctx.fillStyle = '#344d35'; ctx.font = 'bold 31px Georgia';
    wrapText(ctx, messageFor(score), 900, 540, 880, 41);
    ctx.font = '22px Arial'; ctx.fillStyle = '#5b6750'; ctx.fillText('Et toi, feras-tu mieux que moi ?', 540, 978);
    ctx.font = '18px Arial'; ctx.fillText('vivreanyons.fr/jeux/quiz-nyons-histoire-expert/', 540, 1020);
    try {
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
      if (!blob || generation !== cardGeneration || !game.finished) return;
      if (cardObjectUrl) URL.revokeObjectURL(cardObjectUrl);
      cardObjectUrl = URL.createObjectURL(blob);
      const preview = byId('quiz-card-preview'); preview.src = cardObjectUrl; preview.alt = 'Ma carte de résultat : ' + score + ' sur 25 au quiz expert du Nyons d’autrefois';
      const download = byId('quiz-download'); download.href = cardObjectUrl; download.download = 'quiz-nyons-expert-score-' + score + '-sur-25.png'; download.hidden = false;
      byId('quiz-card-area').hidden = false;
    } catch (_) { byId('quiz-share-status').textContent = 'Tu peux toujours copier ton score et partager le lien du quiz.'; }
  }
  renderQuestion(false);
}());

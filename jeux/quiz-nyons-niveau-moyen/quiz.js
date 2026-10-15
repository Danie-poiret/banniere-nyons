/* One local game. No account, storage, server call or automatic publication. */
(function () {
  'use strict';
  const QUESTIONS = [{"id":1,"category":"Marchés et vie locale","question":"Quel jour se tient le grand marché traditionnel de Nyons ?","options":["Mardi","Mercredi","Jeudi","Samedi"],"correct":2,"explanation":"Le jeudi matin est le grand rendez-vous traditionnel du marché nyonsais.","source":"https://www.nyons.com/decouvrir-nyons/art-de-vivre/foires-et-marches/"},{"id":2,"category":"Marchés et vie locale","question":"À quelle période se tient habituellement le marché provençal du dimanche à Nyons ?","options":["Toute l'année","De début mai à mi-septembre","De novembre à mars","Uniquement en décembre"],"correct":1,"explanation":"Le marché provençal du dimanche est saisonnier, de début mai à mi-septembre.","source":"https://www.nyons.com/decouvrir-nyons/art-de-vivre/foires-et-marches/"},{"id":3,"category":"Marchés et vie locale","question":"Quel autre nom porte la place du Docteur Bourdongle ?","options":["Place des Oliviers","Place des Arcades","Place du Pontias","Place Saint-Vincent"],"correct":1,"explanation":"La place du Docteur Bourdongle est également connue comme la place des Arcades.","source":"https://www.nyons.com/decouvrir-nyons/patrimoine/patrimoine-urbain/"},{"id":4,"category":"Marchés et vie locale","question":"Sur quelle place se trouve l'Office de tourisme de Nyons ?","options":["Place Buffaven","Place des Arcades","Place de la Libération","Place Saint-Césaire"],"correct":2,"explanation":"Le bureau de l'Office de tourisme se trouve place de la Libération.","source":"https://www.nyons.com/decouvrir-nyons/office-de-tourisme/"},{"id":5,"category":"Marchés et vie locale","question":"Quel surnom est traditionnellement donné à Nyons en raison de son climat ?","options":["Le Petit Nice","La Petite Venise","Le Petit Avignon","La Petite Florence"],"correct":0,"explanation":"Nyons est surnommée le Petit Nice en raison de son climat doux et ensoleillé.","source":"https://www.nyons.com/decouvrir-nyons/ville-dexception/plus-beaux-detours-de-france/"},{"id":6,"category":"Olives et terroir","question":"Comment s'appelle la variété d'olive emblématique de Nyons ?","options":["Picholine","Aglandau","Tanche","Lucques"],"correct":2,"explanation":"La Tanche est la variété utilisée pour les olives noires de Nyons AOP.","source":"https://www.inao.gouv.fr/en/node/4779"},{"id":7,"category":"Olives et terroir","question":"Quelle protection européenne possèdent les olives noires de Nyons ?","options":["AOP","Label Rouge uniquement","IGP uniquement","Agriculture biologique obligatoire"],"correct":0,"explanation":"Les olives noires de Nyons bénéficient d'une appellation d'origine protégée.","source":"https://www.inao.gouv.fr/en/node/4779"},{"id":8,"category":"Olives et terroir","question":"Quel goût caractérise généralement l'huile d'olive de Nyons ?","options":["Très amer et piquant","Doux et peu amer","Très salé","Fortement fumé"],"correct":1,"explanation":"L'huile de Nyons est connue pour sa douceur et ses arômes délicats.","source":"https://www.inao.gouv.fr/en/node/1963"},{"id":9,"category":"Olives et terroir","question":"Sur quels départements s'étend l'aire de production de l'huile d'olive de Nyons AOP ?","options":["Drôme et Ardèche","Drôme et Isère","Drôme et Vaucluse","Vaucluse et Gard"],"correct":2,"explanation":"L'aire de production concerne le sud de la Drôme et le nord du Vaucluse.","source":"https://www.inao.gouv.fr/en/node/1963"},{"id":10,"category":"Olives et terroir","question":"Quel musée de Nyons présente notamment d'anciennes presses à olives ?","options":["Le Musée de la Soie","Le Musée de l'Olivier","Le Musée des Santons","Le Musée du Ventoux"],"correct":1,"explanation":"Le Musée de l'Olivier de l'espace Vignolis présente l'histoire et les outils de la production oléicole.","source":"https://www.vignolis.fr/fr/espace-vignolis/visite-guidee"},{"id":11,"category":"Patrimoine","question":"Quelle rivière traverse Nyons au pied de son Pont Roman ?","options":["L'Ouvèze","Le Lez","L'Eygues","La Drôme"],"correct":2,"explanation":"Le Pont Roman enjambe l'Eygues.","source":"https://www.nyons.com/decouvrir-nyons/patrimoine/patrimoine-urbain/"},{"id":12,"category":"Patrimoine","question":"Combien de grandes arches possède le Pont Roman de Nyons ?","options":["Une","Deux","Trois","Quatre"],"correct":0,"explanation":"Le Pont Roman est célèbre pour sa grande arche unique.","source":"https://www.nyons.com/decouvrir-nyons/patrimoine/patrimoine-urbain/"},{"id":13,"category":"Patrimoine","question":"Sous quel nom religieux connaît-on également la Tour Randonne ?","options":["Notre-Dame des Victoires","Notre-Dame de Bon-Secours","Sainte-Anne-des-Baronnies","Notre-Dame du Pont"],"correct":1,"explanation":"L'ancienne tour médiévale est devenue la chapelle Notre-Dame de Bon-Secours.","source":"https://www.nyons.com/decouvrir-nyons/patrimoine/patrimoine-urbain/"},{"id":14,"category":"Patrimoine","question":"Comment s'appelle l'église du centre historique de Nyons ?","options":["Saint-Pierre","Sainte-Catherine","Saint-Vincent","Saint-Joseph"],"correct":2,"explanation":"L'église Saint-Vincent fait partie du patrimoine religieux de Nyons.","source":"https://www.nyons.com/decouvrir-nyons/patrimoine/patrimoine-urbain/"},{"id":15,"category":"Patrimoine","question":"Quel jardin présente plus de 180 espèces de plantes aromatiques et médicinales à Nyons ?","options":["Le Jardin des Arômes","Le Parc des Cèdres","Le Jardin du Dauphin","Le Verger des Barons"],"correct":0,"explanation":"Créé en 1983, le Jardin des Arômes est consacré aux plantes de la région.","source":"https://www.nyons.com/vivre-nyons/habitat-et-environnement/parcs-et-jardins/"},{"id":16,"category":"Culture et loisirs","question":"Comment s'appelle le cinéma de Nyons ?","options":["Le Palace","Le Vox","L'Arlequin","Le Régent"],"correct":2,"explanation":"Le cinéma L'Arlequin propose notamment une programmation d'art et d'essai.","source":"https://www.nyons.com/annuaire/cinema-larlequin/"},{"id":17,"category":"Culture et loisirs","question":"Quel est le nom du parc aquatique de Nyons ?","options":["Aquabaronnies","Nyonsoleïado","Aqua-Eygues","Provence Plage"],"correct":1,"explanation":"Nyonsoleïado est le parc aquatique municipal de Nyons.","source":"https://www.nyons.com/vivre-nyons/culture-et-loisirs/parc-aquatique-nyonsoleiado/"},{"id":18,"category":"Culture et loisirs","question":"Où se situe le Théâtre de Verdure de Nyons ?","options":["Sur les hauteurs du Devès","Près de la Tour Randonne","Sur la Promenade de la Digue","Sur la place des Arcades"],"correct":2,"explanation":"Le Théâtre de Verdure se trouve le long de la Promenade de la Digue.","source":"https://www.nyons.com/vivre-nyons/culture-et-loisirs/infrastructures-culturelles/"},{"id":19,"category":"Culture et loisirs","question":"Dans quel bâtiment se trouve la salle Coline Serreau ?","options":["La Maison de Pays","Le cinéma L'Arlequin","L'Office de tourisme","La Scourtinerie"],"correct":0,"explanation":"La salle Coline Serreau est la grande salle de spectacle de la Maison de Pays.","source":"https://www.nyons.com/vivre-nyons/culture-et-loisirs/infrastructures-culturelles/"},{"id":20,"category":"Culture et loisirs","question":"Quel objet traditionnel découvre-t-on à la Scourtinerie de Nyons ?","options":["Des poteries vernissées","Des filtres utilisés dans les pressoirs à huile","Des instruments de musique","Des chaussures en cuir"],"correct":1,"explanation":"Les scourtins sont des filtres utilisés historiquement pour extraire l'huile sous les pressoirs.","source":"https://www.scourtinerie.com/scourtins-filtres"},{"id":21,"category":"Nature et identité locale","question":"Quelle promenade balisée permet de découvrir les oliveraies de Nyons ?","options":["Le sentier des Oliviers","Le sentier des Vautours","Le chemin des Calanques","Le circuit des Dentelles"],"correct":0,"explanation":"Le sentier des Oliviers traverse le patrimoine oléicole nyonsais sur environ 3,9 km.","source":"https://www.nyons.com/vivre-nyons/culture-et-loisirs/sentiers-decouverte/"},{"id":22,"category":"Nature et identité locale","question":"À quel écrivain né à Nyons un circuit de découverte est-il consacré ?","options":["Jean Giono","René Barjavel","Marcel Pagnol","Frédéric Mistral"],"correct":1,"explanation":"Le circuit Barjavel permet de découvrir les lieux de l'enfance de l'écrivain.","source":"https://www.nyons.com/vivre-nyons/culture-et-loisirs/sentiers-decouverte/"},{"id":23,"category":"Nature et identité locale","question":"Qu'appelle-t-on le Pontias à Nyons ?","options":["Un ancien canal","Un vent local","Une variété d'olive","Un quartier de la ville"],"correct":1,"explanation":"Le Pontias est un vent local qui souffle notamment depuis le nord-est.","source":"https://www.nyons.com/decouvrir-nyons/patrimoine/legendes-locales/"},{"id":24,"category":"Nature et identité locale","question":"Quelle balade sur les hauteurs de Nyons permet de traverser garrigues et oliveraies avec une vue sur la vallée de l'Eygues ?","options":["Le sentier du Devès","Le sentier des Ocres","Le sentier des Gorges","Le sentier des Cèdres"],"correct":0,"explanation":"Le circuit du Devès offre des panoramas sur Nyons et sur la vallée.","source":"https://www.nyons.com/vivre-nyons/culture-et-loisirs/sentiers-decouverte/"},{"id":25,"category":"Nature et identité locale","question":"De quel parc naturel régional Nyons est-elle l'un des bourgs-centres ?","options":["Le Luberon","Le Vercors","Les Baronnies provençales","Les Alpilles"],"correct":2,"explanation":"Nyons se trouve dans le Parc naturel régional des Baronnies provençales.","source":"https://www.nyons.com/decouvrir-nyons/ville-dexception/plus-beaux-detours-de-france/"}];
  const QUIZ_URL = 'https://www.vivreanyons.fr/jeux/quiz-nyons-niveau-moyen/';
  function messageFor(score) {
    if (!Number.isInteger(score) || score < 0 || score > 25) throw new RangeError('Score invalide');
    if (score <= 5) return 'Il te reste quelques belles découvertes à faire à Nyons !';
    if (score <= 10) return 'Tu connais déjà quelques secrets de Nyons !';
    if (score <= 15) return 'Pas mal ! Tu connais plutôt bien notre ville.';
    if (score <= 20) return 'Bravo ! Tu es un vrai connaisseur de Nyons !';
    if (score <= 24) return "Impressionnant ! Nyons n'a presque plus de secrets pour toi !";
    return 'PARFAIT ! Tu es un véritable champion de Nyons !';
  }
  function shareText(score) {
    messageFor(score);
    return "🏆 J'ai obtenu " + score + '/25 au quiz CONNAIS-TU VRAIMENT NYONS ? Et toi, feras-tu mieux que moi ? 👉 ' + QUIZ_URL;
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
    byId('quiz-progress').value = game.index + 1;
    byId('quiz-current-score').textContent = game.score + (game.score > 1 ? ' points' : ' point');
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
    byId('quiz-current-score').textContent = game.score + (game.score > 1 ? ' points' : ' point');
    byId('quiz-answer-hint').textContent = 'Réponse enregistrée. Un seul choix est comptabilisé.';
    feedback.classList.toggle('is-wrong', !answer.correct); feedback.hidden = false;
    next.textContent = game.index === 24 ? 'Voir mon résultat →' : 'Question suivante →'; next.hidden = false;
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
    ctx.textAlign = 'center'; ctx.fillStyle = '#52643c'; ctx.font = 'bold 24px Arial'; ctx.fillText('VIVRE À NYONS · LE DÉFI DE PAPY CHRIS', 540, 91);
    ctx.fillStyle = '#253c31'; ctx.font = 'bold 58px Georgia'; ctx.fillText('CONNAIS-TU', 540, 175); ctx.fillText('VRAIMENT NYONS ?', 540, 241);
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
    ctx.font = '18px Arial'; ctx.fillText('vivreanyons.fr/jeux/quiz-nyons-niveau-moyen/', 540, 1020);
    try {
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
      if (!blob || generation !== cardGeneration || !game.finished) return;
      if (cardObjectUrl) URL.revokeObjectURL(cardObjectUrl);
      cardObjectUrl = URL.createObjectURL(blob);
      const preview = byId('quiz-card-preview'); preview.src = cardObjectUrl; preview.alt = 'Ma carte de résultat : ' + score + ' sur 25 au quiz de Nyons';
      const download = byId('quiz-download'); download.href = cardObjectUrl; download.download = 'quiz-nyons-score-' + score + '-sur-25.png'; download.hidden = false;
      byId('quiz-card-area').hidden = false;
    } catch (_) { byId('quiz-share-status').textContent = 'Tu peux toujours copier ton score et partager le lien du quiz.'; }
  }
  renderQuestion(false);
}());

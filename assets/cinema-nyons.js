/* Static, indexable HTML is generated from the agenda dataset. This guard also
   removes expired sessions if an automatic publication is delayed or fails. */
(() => {
  'use strict';
  const guide = document.querySelector('.cinema-guide');
  if (!guide) return;
  const dateLabel = iso => new Intl.DateTimeFormat('fr-FR', {timeZone:'Europe/Paris', day:'numeric', month:'long', year:'numeric', hour:'2-digit', minute:'2-digit'}).format(new Date(iso));
  function refresh() {
    const now = Date.now();
    guide.querySelectorAll('[data-session]').forEach(node => { node.hidden = Date.parse(node.dataset.session) <= now; });
    guide.querySelectorAll('[data-last-session]').forEach(node => { node.hidden = Date.parse(node.dataset.lastSession) <= now; });
    const cards = [...guide.querySelectorAll('.cg-film')];
    cards.forEach(card => {
      const sessions = [...card.querySelectorAll('.cg-times [data-session]')].filter(n => !n.hidden);
      card.hidden = !sessions.length;
      if (!sessions.length) return;
      const first = sessions[0].querySelector('time');
      const next = card.querySelector('.cg-next time');
      next.dateTime = first.dateTime;
      next.textContent = dateLabel(first.dateTime);
      card.querySelector('summary').textContent = `Les ${sessions.length} séances à venir · versions et horaires`;
      // Keep the children's table next screening synchronized after a session ends.
      const url = card.querySelector('.cg-actions a').getAttribute('href');
      guide.querySelectorAll('.cg-children tbody tr').forEach(row => {
        if (row.querySelector('a').getAttribute('href') === url) {
          const time = row.querySelector('time'); time.dateTime = first.dateTime; time.textContent = dateLabel(first.dateTime);
        }
      });
    });
    const list = guide.querySelector('.cg-films');
    cards.sort((a,b) => Date.parse(a.querySelector('.cg-next time').dateTime)-Date.parse(b.querySelector('.cg-next time').dateTime)).forEach(c => list.append(c));
    const hasFilms = cards.some(c => !c.hidden);
    guide.querySelector('.cg-fallback').hidden = hasFilms;
    const programme = guide.querySelector('[data-programme-end]');
    const today = new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/Paris', year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(now));
    const expired = today > programme.dataset.programmeEnd;
    guide.querySelector('.cg-current').hidden = expired;
    guide.querySelector('.cg-pdf').hidden = expired;
    for (const id of ['prochaines-seances','soirees-cinema','enfants-cinema']) {
      const section = guide.querySelector('#'+id);
      const remaining = [...section.querySelectorAll('[data-session],[data-last-session]')].some(n => !n.hidden);
      section.querySelector('.cg-empty').hidden = remaining;
    }
  }
  refresh();
  setInterval(refresh, 60000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
})();


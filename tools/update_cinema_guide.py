#!/usr/bin/env python3
"""Refresh only the permanent cinema guide from the agenda's verified dataset.

No AI, PDF guessing, event regeneration, or changes to film URLs. A newly
detected official PDF is logged for human transcription/verification in the
existing cinema-programme.json source, not accepted as invented sessions.
"""
import argparse
from datetime import datetime, date
import html
import json
from pathlib import Path
import re
import unicodedata
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path('infos-pratiques-nyons/cinema-nyons/index.html')
DATA_URL = 'https://raw.githubusercontent.com/Danie-poiret/agenda-nyons/main/cinema-programme.json'
CONFIG_URL = 'https://ws.ticketingcine.com/config.js?site_id=EMS0177'
OFFICIAL = 'https://www.cinema-arlequin.fr/'
BOOKING = 'https://www.ticketingcine.com/cine/LTGJT7N5.html'
TZ = ZoneInfo('Europe/Paris')
MONTHS = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
BEGIN, END = '<!-- CINEMA-AUTO:START -->', '<!-- CINEMA-AUTO:END -->'
E = html.escape

def fmt(raw):
    d = date.fromisoformat(raw)
    return f'{d.day} {MONTHS[d.month]} {d.year}'

def stamp(s):
    return datetime.fromisoformat(s['date'] + 'T' + s['time']).replace(tzinfo=TZ)

def slug(text):
    raw = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.sub('[^a-z0-9]+', '-', raw).strip('-')[:82].rstrip('-')

def film_url(f):
    # Exactly the agenda generator's route, derived BEFORE filtering sessions.
    title = f.get('event_title') or 'Cinéma — ' + f['title']
    return 'https://agenda.vivreanyons.fr/evenements/' + slug(title) + '-' + min(s['date'] for s in f['sessions']) + '/'

def validate(data):
    start, end = date.fromisoformat(data['period_start']), date.fromisoformat(data['period_end'])
    verified = date.fromisoformat(data['verified_on'])
    if end < start or not data['source_pdf'].startswith('https://documents.monnaie-services.com/site_file/EMS0177/'):
        raise ValueError('Période ou source officielle invalide')
    seen = set()
    for f in data['films']:
        if not f['title'].strip() or not f['sessions'] or f['title'] in seen:
            raise ValueError('Film vide ou titre en doublon')
        seen.add(f['title'])
        period = f.get('programme', data)
        a, b = date.fromisoformat(period['period_start']), date.fromisoformat(period['period_end'])
        sessions = set()
        for s in f['sessions']:
            dt = stamp(s)
            if not a <= dt.date() <= b or not re.fullmatch(r'\d{2}:\d{2}', s['time']):
                raise ValueError('Séance hors période : ' + f['title'])
            key = (s['date'], s['time'])
            if key in sessions:
                raise ValueError('Séance en doublon : ' + f['title'])
            sessions.add(key)
    return verified

def future_films(data, now):
    result = []
    for f in data['films']:
        # Archives stay in the shared source and keep their existing URLs.
        if f.get('programme', data)['period_end'] < now.date().isoformat():
            continue
        sessions = sorted((s for s in f['sessions'] if stamp(s) > now), key=stamp)
        if sessions:
            result.append((f, sessions))
    return sorted(result, key=lambda pair: (stamp(pair[1][0]), pair[0]['title'].casefold()))

def when(s):
    return fmt(s['date']) + ' à ' + s['time'].replace(':', ' h ')

def table(caption, headings, rows, cls=''):
    return '<div class="cg-table ' + cls + '"><table><caption>' + E(caption) + '</caption><thead><tr>' + ''.join('<th scope="col">' + E(h) + '</th>' for h in headings) + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'

def render(data, now):
    films = future_films(data, now)
    period = f"du {fmt(data['period_start'])} au {fmt(data['period_end'])}"
    out = ['<section id="programme-cinema" class="cg-programme" data-programme-end="' + data['period_end'] + '"><h2>🎬 Le programme du cinéma L’Arlequin à Nyons</h2>']
    expired = data['period_end'] < now.date().isoformat()
    out.append('<p class="cg-current"' + (' hidden' if expired else '') + '>Programme ' + period + '. Horaires issus du programme officiel vérifié ; les séances déjà terminées sont retirées de cette sélection.</p>')
    out.append('<p class="cg-fallback"' + ('' if not films else ' hidden') + '>Le prochain programme vérifié n’est pas encore disponible ici. Consulte <a href="' + OFFICIAL + '">le programme et la billetterie de L’Arlequin</a> pour les séances actualisées.</p>')
    out.append('<p class="cg-pdf"' + (' hidden' if expired else '') + '><a href="' + E(data['source_pdf'], quote=True) + '">📄 Programme officiel en PDF — ' + period + '</a></p>')
    out.append('<p><a href="https://agenda.vivreanyons.fr/cinema/">Toutes les fiches cinéma de l’agenda</a> · <a href="https://agenda.vivreanyons.fr/">Les autres sorties à Nyons</a></p><div class="cg-films">')
    for f, sessions in films:
        first = sessions[0]
        poster = f.get('poster', '')
        if poster.startswith('/'):
            poster = 'https://agenda.vivreanyons.fr' + poster
        last = stamp(sessions[-1]).isoformat()
        out.append('<section class="cg-film" data-last-session="' + last + '"><div class="cg-film-top"><img src="' + E(poster, quote=True) + '" alt="' + E(f.get('poster_alt', 'Affiche de ' + f['title']), quote=True) + '" width="120" height="174" loading="lazy" decoding="async"><div><h3>' + E(f['title']) + '</h3><p class="cg-next"><strong>Prochaine séance : <time datetime="' + stamp(first).isoformat() + '">' + when(first) + '</time></strong></p><p>' + E(f.get('duration') or 'Durée non précisée dans le programme') + (' · ' + E(f['age']) if f.get('age') else '') + '</p></div></div><p>' + E(f['description']) + '</p>')
        out.append('<details><summary>Les ' + str(len(sessions)) + ' séances à venir · versions et horaires</summary><ul class="cg-times">')
        for s in sessions:
            out.append('<li data-session="' + stamp(s).isoformat() + '"><time datetime="' + stamp(s).isoformat() + '">' + when(s) + '</time> · ' + E(s['version']) + (' · ' + E(str(s['price'])) + ' €' if s.get('price') else '') + '</li>')
        out.append('</ul></details>')
        if f.get('special_note') or f.get('price_note'):
            out.append('<p class="cg-note">' + E(' '.join(f[k] for k in ('special_note', 'price_note') if f.get(k))) + '</p>')
        if f.get('poster_credit'):
            out.append('<p class="cg-note">' + E(f['poster_credit']) + '</p>')
        out.append('<div class="cg-actions"><a href="' + film_url(f) + '">Fiche complète du film</a><a href="' + OFFICIAL + '">🎟️ Séances et réservation sur le site officiel</a></div></section>')
    out.append('</div></section>')
    out.append('<section id="prochaines-seances"><h2>📅 Les séances des prochains jours</h2><p>Heures locales à Nyons, y compris après le changement d’heure du 25 octobre. Deux films peuvent commencer ensemble : L’Arlequin possède deux salles.</p>')
    all_sessions = sorted(((s, f) for f, sessions in films for s in sessions), key=lambda pair: (stamp(pair[0]), pair[1]['title']))
    days = sorted({s['date'] for s, _ in all_sessions})[:7]
    rows = []
    for s, f in all_sessions:
        if s['date'] in days:
            rows.append('<tr data-session="' + stamp(s).isoformat() + '"><th scope="row">' + fmt(s['date']) + '</th><td>' + E(s['time']) + '</td><td><a href="' + film_url(f) + '">' + E(f['title']) + '</a></td><td>' + E(s['version']) + '</td></tr>')
    out.append(table('Les sept prochains jours de projection du programme vérifié', ['Date', 'Heure', 'Film', 'Version'], rows, 'cg-sessions'))
    out.append('<p class="cg-empty"' + ('' if not rows else ' hidden') + '>Aucune séance future vérifiée à afficher. Vérifie les horaires auprès du cinéma.</p></section>')
    out.append('<section id="soirees-cinema"><h2>🌟 Les soirées et événements spéciaux</h2><p>Pour une soirée avec repas, appelle suffisamment tôt. Les horaires d’une séance ordinaire ne donnent pas automatiquement accès à l’animation spéciale.</p>')
    specials = [(f, ss) for f, ss in films if f.get('special_note') or f.get('price_note') or f.get('price') or f['title'] in ('Scream', 'Suspiria')]
    for f, ss in specials:
        # Cars has regular screenings as well as its specifically dated animation.
        chosen = [s for s in ss if s.get('price') == 5] if f['title'] == 'Cars' else ss
        if not chosen:
            continue
        s = chosen[0]
        note = ' '.join(f[k] for k in ('special_note', 'price_note') if f.get(k))
        if not note:
            note = ('Ciné-goûter : 5 €, réservation au cinéma.' if f.get('price') == 5 else f.get('age', 'Tarif à confirmer auprès du cinéma.'))
        out.append('<div class="cg-special" data-last-session="' + stamp(chosen[-1]).isoformat() + '"><h3>' + E(f['title']) + '</h3><p><strong>' + when(s) + '</strong> · ' + E(s['version']) + '</p><p>' + E(note) + '</p></div>')
    out.append('<p class="cg-empty"' + ('' if not specials else ' hidden') + '>Aucune animation future vérifiée. Consulte le cinéma pour les prochains rendez-vous.</p></section>')
    out.append('<section id="enfants-cinema"><h2>👨‍👩‍👧 Le cinéma avec les enfants</h2><p>Pour une première sortie, regarde la durée et l’âge conseillé : le tarif enfant ne signifie pas que tous les films conviennent aux petits. Les restrictions d’âge annoncées figurent sur les fiches des films concernés.</p>')
    children = [(f, ss) for f, ss in films if f.get('age', '').startswith('À partir')]
    rows = ['<tr data-last-session="' + stamp(ss[-1]).isoformat() + '"><th scope="row"><a href="' + film_url(f) + '">' + E(f['title']) + '</a></th><td>' + E(f['age']) + '<br>' + E(f.get('duration') or 'Durée non précisée') + '</td><td class="cg-child-next"><time datetime="' + stamp(ss[0]).isoformat() + '">' + when(ss[0]) + '</time></td></tr>' for f, ss in children]
    out.append(table('Les prochaines séances des films avec un âge conseillé annoncé', ['Film', 'Âge / durée', 'Prochaine séance'], rows, 'cg-children'))
    out.append('<p>Les ciné-goûters et autres séances spéciales peuvent avoir un tarif distinct. Vérifie les conditions du rendez-vous et la réservation auprès du cinéma.</p><p class="cg-empty"' + ('' if not children else ' hidden') + '>Aucune séance jeune public future vérifiée pour le moment.</p></section>')
    out.append('<p class="cinema-source">Source commune avec les fiches de l’agenda : programme officiel de L’Arlequin, ' + period + '. Données vérifiées le ' + fmt(data['verified_on']) + '. Les séances peuvent être modifiées par le cinéma.</p>')
    return '\n'.join(out)

def get(url):
    with urlopen(Request(url, headers={'User-Agent': 'VivreANyons-Cinema/1.0'}), timeout=25) as r:
        return r.read().decode('utf-8')

def official_pdf(config_text):
    match = re.search(r'\bconst\s+gl_config\s*=\s*', config_text)
    if not match:
        raise ValueError('Configuration publique du programme non trouvée')
    data = json.JSONDecoder().raw_decode(config_text[match.end():].lstrip())[0]
    def walk(node):
        if isinstance(node, dict):
            action = node.get('action_button', {})
            link = action.get('link', {})
            if action.get('active') and link.get('file_url', '').endswith('.pdf'):
                return link['file_url']
            for value in node.values():
                result = walk(value)
                if result:
                    return result
        elif isinstance(node, list):
            for value in node:
                result = walk(value)
                if result:
                    return result
    result = walk(data)
    if not result or not result.startswith('https://documents.monnaie-services.com/site_file/EMS0177/'):
        raise ValueError('PDF public officiel non trouvé')
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, help='Verified local source for offline tests')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--now', help='ISO datetime for expiry/DST tests')
    args = parser.parse_args()
    now = datetime.fromisoformat(args.now).astimezone(TZ) if args.now else datetime.now(TZ)
    root = args.root
    cache = root / 'assets/cinema-nyons-data.json'
    status_file = root / 'assets/cinema-nyons-status.json'
    status = {'checked_at': now.isoformat(), 'source': DATA_URL, 'errors': []}
    try:
        data = json.loads(args.data.read_text(encoding='utf-8') if args.data else get(DATA_URL))
        validate(data)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    except Exception as exc:
        status['errors'].append('Récupération : ' + str(exc))
        if not cache.exists():
            raise
        data = json.loads(cache.read_text(encoding='utf-8'))
        validate(data)
    if not args.data:
        try:
            pdf = official_pdf(get(CONFIG_URL))
            status['official_pdf'] = pdf
            if pdf != data['source_pdf']:
                status['errors'].append('Nouveau PDF détecté : transcription et comparaison requises dans la source cinéma existante.')
        except Exception as exc:
            status['errors'].append('Contrôle du PDF : ' + str(exc))
    status['period_end'] = data['period_end']
    if data['period_end'] < now.date().isoformat():
        status['errors'].append('Programme expiré : repli officiel affiché, prochain programme vérifié attendu.')
    target = root / PAGE
    original = target.read_text(encoding='utf-8')
    before, tail = original.split(BEGIN, 1)
    _, after = tail.split(END, 1)
    target.write_text(before + BEGIN + '\n' + render(data, now) + '\n' + END + after, encoding='utf-8')
    status_file.write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(status, ensure_ascii=False))

if __name__ == '__main__':
    main()


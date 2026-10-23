"""Refresh only the existing manifestations page from the existing Nyons agenda.

Run manually before publication. No agenda, URL, scheduler or global SEO change.
On source failure, prune the previous snapshot against today's Paris clock.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import html
import json
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'evenements-nyons/manifestations-locales/index.html'
FEED = 'https://agenda.vivreanyons.fr/'


def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'VivreAnyons-manifestations/1.0', 'Cache-Control': 'no-cache'}), timeout=25) as response:
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError('Oversized agenda source')
        return body.decode('utf-8')


def js(root, payload):
    script = "const a=require('./assets/manifestations.js'),fs=require('node:fs'),p=JSON.parse(fs.readFileSync(0,'utf8'));const d=p.feed?{events:a.normalize(p.feed,p.published,p.prices)}:p.data;const r=a.select(d,new Date(p.at));console.log(JSON.stringify({data:d,result:r,html:a.render(r)}));"
    run = subprocess.run(['node', '-e', script], input=json.dumps(payload), cwd=root, text=True, capture_output=True, check=True, encoding='utf-8')
    return json.loads(run.stdout)


def replace(source, pattern, value):
    source, count = re.subn(pattern, lambda _: value, source, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Missing manifestations marker: ' + pattern)
    return source


def refresh(root=ROOT, fixture=None, at=None):
    now = datetime.fromisoformat(at) if at else datetime.now(ZoneInfo('Europe/Paris'))
    if now.tzinfo is None:
        raise ValueError('A timezone is required')
    stamp = now.isoformat(timespec='minutes')
    target = root / PAGE
    source = target.read_text(encoding='utf-8')
    old = json.loads(re.search(r'<script type="application/json" id="manifestations-data">(.*?)</script>', source, re.S)[1])
    status = 'available'
    try:
        if fixture:
            raw = json.loads(fixture.read_text(encoding='utf-8'))
            feed, published, prices = raw['feed'], raw['published'], raw.get('prices', {})
        else:
            with ThreadPoolExecutor(max_workers=2) as pool:
                texts = list(pool.map(fetch, [FEED + 'agenda.json', FEED + 'sitemap.xml']))
            feed = json.loads(texts[0])
            published = re.findall(r'<loc>([^<]+)</loc>', texts[1])
            prices = {}
        if not isinstance(feed.get('events'), list) or not published:
            raise ValueError('Invalid agenda or publication index')
        draft = js(root, {'feed': feed, 'published': published, 'at': stamp})
        # Read prices from the linked cinema sheets, never from a guessed tariff.
        if not fixture:
            cinema = [e for e in draft['result']['upcoming'] if e['kind'] == 'cinema']
            def price(e):
                try:
                    page = fetch(e['url'])
                    match = re.search(r'<h2[^>]*>Tarifs et réservation</h2>\s*<p[^>]*>(.*?)</p>', page, re.S)
                    if match:
                        text = html.unescape(re.sub('<[^>]+>', '', match[1])).strip().split('. ')[0].rstrip('.')
                        if len(text) < 500:
                            return e['url'], text
                except Exception:
                    pass
                return e['url'], ''
            with ThreadPoolExecutor(max_workers=4) as pool:
                prices.update(dict(pool.map(price, cinema)))
        built = js(root, {'feed': feed, 'published': published, 'prices': prices, 'at': stamp})
        data = built['data']
        data['sourceUpdated'] = feed.get('updated_at', stamp)
    except Exception as error:
        print('Agenda unavailable; filtering previous snapshot: ' + str(error))
        status, data = 'cached', old
    day = now.astimezone(ZoneInfo('Europe/Paris')).date().isoformat()
    data['events'] = [e for e in data.get('events', []) if e['end'] >= day]
    data['status'] = status
    data['generatedAt'] = stamp
    built = js(root, {'data': data, 'at': stamp})
    source = replace(source, r'<!-- MANIFESTATIONS_RESULTS_START -->.*?<!-- MANIFESTATIONS_RESULTS_END -->', '<!-- MANIFESTATIONS_RESULTS_START -->' + built['html'] + '<!-- MANIFESTATIONS_RESULTS_END -->')
    serialized = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    source = replace(source, r'<script type="application/json" id="manifestations-data">.*?</script>', '<script type="application/json" id="manifestations-data">' + serialized + '</script>')
    label = 'Sélection actualisée le ' + day[8:] + '/' + day[5:7] + '/' + day[:4] + ' à ' + now.astimezone(ZoneInfo('Europe/Paris')).strftime('%H h %M') + ' (heure de Paris).'
    if status == 'cached':
        label += ' Source momentanément indisponible : dernières annonces conservées, dates dépassées écartées.'
    source = replace(source, r'<p class="sorties-source" data-sorties-updated>.*?</p>', '<p class="sorties-source" data-sorties-updated>' + html.escape(label) + '</p>')
    count = len(built['result']['upcoming'])
    source = replace(source, r'<p class="sorties-status" data-sorties-status[^>]*>.*?</p>', '<p class="sorties-status" data-sorties-status role="status" aria-live="polite">' + str(count) + ' prochains rendez-vous à Nyons.</p>')
    if target.read_text(encoding='utf-8') != source:
        target.write_text(source, encoding='utf-8', newline='')
    print(json.dumps({'page': PAGE, 'events': count, 'ongoing': len(built['result']['ongoing']), 'sourceStatus': status, 'at': stamp}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', type=Path)
    parser.add_argument('--at')
    args = parser.parse_args()
    refresh(fixture=args.fixture, at=args.at)

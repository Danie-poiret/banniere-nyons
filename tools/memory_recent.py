"""Keep the static Memory hub recent cards in the same publication as each story.

The committed catalogue makes a normal publication incremental. A full rebuild
is reserved for repairs and CI; original publication dates are never invented.
"""
import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET

from lxml import html as dom

SITE = 'https://www.vivreanyons.fr'
HUB = 'memoire-de-france/index.html'
CATALOG = 'tools/memory-recent.json'
START = '<!-- memory-recent:start -->'
END = '<!-- memory-recent:end -->'
LIMIT = 6


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def read(root, path, extra):
    return extra[path] if path in extra else (root / path).read_text(encoding='utf-8')


def route(path):
    return '/' + path.removesuffix('index.html')


def owner(path, config):
    if '\\' in path or any(part in ('.', '..') for part in path.split('/')):
        return None
    for city in config['cities']:
        if path in {row['path'] for row in city['legacy']} or (
            path.startswith(city['path'] + '/') and
            len(Path(path).parts) == 5 and path.endswith('/index.html')
        ):
            return city
    return None


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        return None


def record(root, path, source, config):
    city = owner(path, config)
    if not city:
        return None
    page = dom.fromstring(source)
    if any('noindex' in v.lower() for v in page.xpath('//meta[@name="robots"]/@content')):
        return None
    articles = []
    for script in page.xpath('//script[@type="application/ld+json"]/text()'):
        for item in nodes(json.loads(script)):
            types = item.get('@type', [])
            if types == 'Article' or isinstance(types, list) and 'Article' in types:
                articles.append(item)
    if not articles:
        return None
    published = articles[0].get('datePublished')
    # Old stories without a documented date remain in their city, not "recent".
    if not timestamp(published):
        return None
    assert page.xpath('//link[@rel="canonical"]/@href') == [SITE + route(path)], 'Wrong recent story canonical: ' + path
    headings = page.xpath('//h1')
    assert len(headings) == 1, 'One story H1 required: ' + path
    images = page.xpath('//main//img[@src]')
    assert images, 'Missing recent story image: ' + path
    image = images[0]
    src = urlsplit(image.get('src'))
    assert not src.netloc and src.path.startswith('/'), 'Local recent image required: ' + path
    assert (root / unquote(src.path).lstrip('/')).is_file(), 'Missing recent image file: ' + path
    assert all(image.get(k) for k in ('alt', 'width', 'height')), 'Incomplete recent image: ' + path
    title = ' '.join(headings[0].itertext()).strip()
    descriptions = page.xpath('//meta[@name="description"]/@content')
    return {
        'path': path, 'city_id': city['id'], 'city': city['name'],
        'department': city['department'], 'datePublished': published,
        'title': ' '.join(title.split()), 'summary': descriptions[0] if descriptions else title,
        'image': {key: image.get(key) for key in ('src', 'alt', 'width', 'height')},
    }


def discover(root, config, extra):
    paths = {row['path'] for city in config['cities'] for row in city['legacy']}
    for city in config['cities']:
        folder = root / city['path']
        if folder.is_dir():
            paths.update(p.relative_to(root).as_posix() for p in folder.glob('*/index.html'))
    paths.update(path for path in extra if owner(path, config))
    return sorted(paths)


def select_recent(records, sitemap, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    entries = ET.fromstring(sitemap).findall('{*}url/{*}loc')
    order = {entry.text: i for i, entry in enumerate(entries)}
    eligible = [r for r in records if timestamp(r['datePublished']) <= now]
    # Later sitemap additions break ties on date-only publications.
    return sorted(eligible, key=lambda r: (
        -timestamp(r['datePublished']).timestamp(),
        -order.get(SITE + route(r['path']), -1), r['path']
    ))[:LIMIT]


def card(item):
    esc = lambda value: html.escape(str(value), quote=True)
    image = ' '.join(f'{key}="{esc(value)}"' for key, value in item['image'].items())
    return (
        '<article class="card memory-card"><a href="' + esc(route(item['path'])) + '">'
        '<div class="memory-image"><img ' + image + ' loading="lazy" decoding="async"></div>'
        '<div class="memory-card-body"><div class="memory-location">' + esc(item['city']) + ' · ' + esc(item['department']) + '</div>'
        '<h3>' + esc(item['title']) + '</h3><p>' + esc(item['summary']) + '</p>'
        '<span class="memory-read">Lire l’histoire <span aria-hidden="true">→</span></span>'
        '</div></a></article>'
    )


def render_hub(source, selected):
    block = START + '<div class="memory-grid memory-recent-grid">' + ''.join(card(r) for r in selected) + '</div>' + END
    if START in source or END in source:
        assert source.count(START) == source.count(END) == 1, 'Ambiguous recent markers'
        return re.sub(re.escape(START) + r'[\s\S]*?' + re.escape(END), lambda _: block, source)
    # One-time migration: replace only the old recent grid, preserving the rest.
    page = dom.fromstring(source)
    grids = page.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," memory-recent-grid ")]')
    assert len(grids) == 1, 'One recent grid required'
    opening = re.search(r'<div\b[^>]*class=["\'][^"\']*\bmemory-recent-grid\b[^"\']*["\'][^>]*>', source)
    assert opening, 'Recent grid opening missing'
    depth = 1
    for tag in re.finditer(r'</?div\b[^>]*>', source[opening.end():]):
        depth += -1 if tag[0].startswith('</') else 1
        if depth == 0:
            end = opening.end() + tag.end()
            return source[:opening.start()] + block + source[end:]
    raise AssertionError('Unclosed recent grid')


def plan(root, config, extra=None, rebuild=False):
    extra = extra or {}
    if rebuild:
        assert all(c['path'] + '/index.html' in extra or (root / (c['path'] + '/index.html')).is_file() for c in config['cities']), 'Rebuild requires all registered city indexes'
        paths = discover(root, config, extra)
        records = {}
    else:
        assert (root / CATALOG).is_file(), 'Refresh tools/memory-recent.json from GitHub; rebuild only from a complete Memory checkout'
        data = json.loads(read(root, CATALOG, extra))
        assert data['version'] == 1
        records = {r['path']: r for r in data['articles']}
        paths = [path for path in extra if owner(path, config)]
    for path in paths:
        item = record(root, path, read(root, path, extra), config)
        if item:
            records[path] = item
        else:
            records.pop(path, None)
    catalogue = json.dumps({'version': 1, 'articles': [records[p] for p in sorted(records)]}, ensure_ascii=False, indent=2) + '\n'
    selected = select_recent(list(records.values()), read(root, 'sitemap.xml', extra))
    hub = render_hub(read(root, HUB, extra), selected)
    return {p: s for p, s in ((CATALOG, catalogue), (HUB, hub))
            if not (root / p).is_file() or s != read(root, p, extra)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--refresh', action='append', default=[], metavar='ARTICLE/index.html')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    config = json.loads((root / 'tools/memory-cities.json').read_text(encoding='utf-8'))
    extra = {}
    for path in args.refresh:
        assert owner(path, config), 'Not a registered Memory story: ' + path
        extra[path] = (root / path).read_text(encoding='utf-8')
    changes = plan(root, config, extra, rebuild=args.rebuild or args.check)
    print(json.dumps({'changes': sorted(changes)}, ensure_ascii=False))
    if args.check:
        return bool(changes)
    for path, source in changes.items():
        (root / path).write_text(source, encoding='utf-8', newline='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

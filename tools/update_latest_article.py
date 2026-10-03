"""Refresh the three homepages from the most recently published Article.

Run before publishing any new article: python tools/update_latest_article.py
Only datePublished determines recency; editing dateModified does not.
"""
import argparse
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.images, self.data, self.capture, self.buffer = [], [], False, []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img':
            self.images.append(attrs)
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.capture, self.buffer = True, []

    def handle_data(self, value):
        if self.capture:
            self.buffer.append(value)

    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.capture = False
            try:
                self.data.append(json.loads(''.join(self.buffer)))
            except json.JSONDecodeError:
                pass


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def update(root):
    sitemap = ET.parse(root / 'sitemap.xml')
    positions = {urlsplit(e.text).path: i for i, e in enumerate(sitemap.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'))}
    candidates = []
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = [name for name in subdirs if name not in {'.git', '.github', 'assets', 'tools', 'vivreanyons-test', 'banniere-nyons', '_pont_upload'}]
        if 'index.html' not in files or Path(directory) == root:
            continue
        file = Path(directory) / 'index.html'
        page = Page(file.read_text(encoding='utf-8'))
        path = '/' + file.parent.relative_to(root).as_posix() + '/'
        for item in objects(page.data):
            kind = item.get('@type')
            if not (kind == 'Article' or isinstance(kind, list) and 'Article' in kind):
                continue
            published = item.get('datePublished', '')
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T.*)?', published):
                continue
            headline, description = item.get('headline'), item.get('description')
            if not headline or not description:
                continue
            images = item.get('image', [])
            images = images if isinstance(images, list) else [images]
            image_paths = [urlsplit(image.get('url', '') if isinstance(image, dict) else image).path for image in images]
            photo = next((image for image in page.images if urlsplit(image.get('src', '')).path in image_paths and image.get('alt')), None)
            candidates.append((published, positions.get(path, -1), path, headline, description, photo))
    if not candidates:
        raise ValueError('No dated Article found; homepages were not changed.')
    published, _, path, headline, description, photo = max(candidates, key=lambda item: item[:3])
    if not photo:
        raise ValueError('Missing latest article image with alt: ' + path)
    year, month, day = published[:10].split('-')
    months = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
    date = f'{int(day)} {months[int(month)-1]} {year}'
    escape = lambda value: html.escape(str(value), quote=True)
    for prefix in ['', '/vivreanyons-test', '/banniere-nyons/vivreanyons-test']:
        file = root / prefix.lstrip('/') / 'index.html'
        source = file.read_text(encoding='utf-8')
        image_path = urlsplit(photo['src']).path
        dimensions = ''.join(f' {key}="{escape(photo[key])}"' for key in ['width', 'height'] if key in photo)
        card = f'''<section class="new-article" aria-labelledby="new-article-title" data-latest-article="{escape(path)}">
<div><div class="kicker">Dernier article · <time datetime="{escape(published[:10])}">{date}</time></div>
<h2 id="new-article-title"><a class="new-article-link" href="{escape(prefix + path)}">{escape(headline)}</a></h2>
<p>{escape(description)}</p></div>
<a href="{escape(prefix + path)}" tabindex="-1" aria-hidden="true"><img src="{escape(prefix + image_path)}" alt="{escape(photo['alt'])}"{dimensions} decoding="async"></a>
</section>'''
        source, count = re.subn(r'<section class="new-article"[^>]*>.*?</section>', lambda match: card, source, count=1, flags=re.S)
        if count != 1:
            raise ValueError('Cannot find latest-article card: ' + str(file))
        if '.new-article h2 a{' not in source:
            source = source.replace('.new-article-link{font-weight:800}', '.new-article-link{font-weight:800}.new-article h2 a{color:inherit;text-decoration:none}.new-article h2 a:hover,.new-article h2 a:focus-visible{text-decoration:underline;text-underline-offset:4px}')
        file.write_text(source, encoding='utf-8')
    print(f'Latest article: {published[:10]} — {headline} ({path})')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    update(parser.parse_args().root.resolve())

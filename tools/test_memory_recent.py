"""Publication regressions: a story must not go live with a stale recent list."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from lxml import html

import add_memory_article
import memory_recent as recent
import update_memory_cities as memory


class MemoryPublicationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.city = {'id': 'marseille', 'name': 'Marseille',
                     'path': 'Provence-Alpes-Cote-dAzur/Bouches-du-Rhone/Marseille',
                     'department': 'Bouches-du-Rhône', 'region': 'Provence-Alpes-Côte d’Azur',
                     'existing': True, 'legacy': []}
        self.config = {'version': 1, 'cities': [self.city]}
        self.old = self.city['path'] + '/ancien/index.html'
        self.new = self.city['path'] + '/nouveau/index.html'
        self.write('tools/memory-cities.json', json.dumps(self.config))
        self.write('assets/photo.png', 'fixture')
        self.write('index.html', '<h1>Accueil principal conservé</h1>')
        self.hub = ('<html><head><link rel="canonical" href="' + recent.SITE + '/memoire-de-france/"></head><body>'
                    '<main><section id="editorial"><p>Sélection éditoriale et crédit inchangés</p></section>'
                    '<div class="memory-grid memory-recent-grid"><article>Ancienne sélection</article></div>'
                    '</main><footer>Navigation conservée</footer></body></html>')
        nav = '<a href="/' + self.city['path'] + '/">Marseille</a> <span>(1)</span>'
        self.write(recent.HUB, self.hub.replace('</main>', nav + '</main>'))
        for parent in ['Provence-Alpes-Cote-dAzur', 'Provence-Alpes-Cote-dAzur/Bouches-du-Rhone']:
            self.write(parent + '/index.html', '<html><head><link rel="canonical" href="' + recent.SITE + '/' + parent + '/"></head><body><main>' + nav + '</main></body></html>')
        self.write(self.old, self.story(self.old, '2026-01-01'))
        old_record = memory.article(self.root, self.old, '', {})
        schema = {'@context': 'https://schema.org', '@type': 'ItemList', 'numberOfItems': 1,
                  'itemListElement': [{'@type': 'ListItem', 'position': 1, 'url': recent.SITE + recent.route(self.old), 'name': 'Ancien'}]}
        city_html = ('<html><head><link rel="canonical" href="' + recent.SITE + '/' + self.city['path'] + '/">'
                     '<script type="application/ld+json">' + json.dumps(schema) + '</script></head><body><main>'
                     '<p class="city-count">1 récit</p><div class="memory-grid">' + memory.card(old_record, self.city) + '</div></main></body></html>')
        self.write(self.city['path'] + '/index.html', city_html)
        self.write('sitemap.xml', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>' + recent.SITE + recent.route(self.old) + '</loc></url></urlset>')
        self.apply(recent.plan(self.root, self.config, rebuild=True))

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding='utf-8')

    def apply(self, changes):
        for path, value in changes.items():
            self.write(path, value)

    def story(self, path, published, modified='2026-11-06', title='Récit de Marseille'):
        schema = {'@context': 'https://schema.org', '@type': ['Article'], 'datePublished': published, 'dateModified': modified}
        return ('<html><head><link rel="canonical" href="' + recent.SITE + recent.route(path) + '">'
                '<meta name="description" content="Une histoire &amp; des souvenirs.">'
                '<script type="application/ld+json">' + json.dumps(schema) + '</script></head>'
                '<body><main><h1>' + title + '</h1><img src="/assets/photo.png" alt="Vue ancienne" width="400" height="600"></main></body></html>')

    def links(self, source):
        return html.fromstring(source).xpath('//div[contains(@class,"memory-recent-grid")]/article/a/@href')

    def test_publication_updates_city_hub_counts_and_sitemap_together(self):
        homepage = (self.root / 'index.html').read_bytes()
        source = self.story(self.new, '2026-02-01')
        changes = add_memory_article.prepare(self.root, 'marseille', 'nouveau', source)
        self.assertIn(self.new, changes)
        self.assertEqual(self.links(changes[recent.HUB])[0], recent.route(self.new))
        city = html.fromstring(changes[self.city['path'] + '/index.html'])
        self.assertEqual(city.xpath('//div[@class="memory-grid"]/article/a/@href')[0], recent.route(self.new))
        self.assertIn('(2)', changes[recent.HUB])
        self.assertIn(recent.SITE + recent.route(self.new), changes['sitemap.xml'])
        self.assertIn(recent.CATALOG, changes)
        self.assertNotIn('index.html', changes)
        self.assertEqual((self.root / 'index.html').read_bytes(), homepage)
        self.assertLessEqual(len(changes), 7)

    def test_date_modified_does_not_make_an_old_story_recent(self):
        source = self.story(self.new, '2026-02-01', modified='2026-02-01')
        self.write(self.new, source)
        changes = recent.plan(self.root, self.config, {self.new: source})
        self.apply(changes)
        before = self.links((self.root / recent.HUB).read_text(encoding='utf-8'))
        old_updated = self.story(self.old, '2026-01-01', modified='2030-01-01')
        changes = recent.plan(self.root, self.config, {self.old: old_updated})
        self.assertNotIn(recent.HUB, changes)
        self.assertEqual(before[0], recent.route(self.new))

    def test_same_day_uses_sitemap_addition_order_and_excludes_future(self):
        records = []
        for slug, date in [('a', '2026-01-01'), ('b', '2026-01-01'), ('future', '2099-01-01')]:
            path = self.city['path'] + '/' + slug + '/index.html'
            records.append(recent.record(self.root, path, self.story(path, date), self.config))
        sitemap = '<urlset>' + ''.join('<url><loc>' + recent.SITE + recent.route(r['path']) + '</loc></url>' for r in records) + '</urlset>'
        selected = recent.select_recent(records, sitemap, datetime(2026, 2, 1, tzinfo=timezone.utc))
        self.assertEqual([r['path'] for r in selected], [records[1]['path'], records[0]['path']])

    def test_migration_preserves_editorial_and_is_idempotent(self):
        source = (self.root / recent.HUB).read_text(encoding='utf-8')
        self.assertIn('<section id="editorial"><p>Sélection éditoriale et crédit inchangés</p></section>', source)
        self.assertIn('<footer>Navigation conservée</footer>', source)
        self.assertEqual(source.count(recent.START), 1)
        self.assertEqual(recent.plan(self.root, self.config, rebuild=True), {})

    def test_fast_publication_never_needs_other_article_files(self):
        (self.root / self.old).unlink()
        changes = add_memory_article.prepare(self.root, 'marseille', 'nouveau', self.story(self.new, '2026-02-01').replace('["Article"]', '"Article"'))
        self.assertEqual(len(self.links(changes[recent.HUB])), 2)

    def test_refresh_detects_a_changed_title_and_keeps_original_date(self):
        updated = self.story(self.old, '2026-01-01', title='Titre corrigé &amp; précisé')
        self.write(self.old, updated)
        changes = recent.plan(self.root, self.config, rebuild=True)
        self.assertIn(recent.HUB, changes)
        self.assertIn('Titre corrigé &amp; précisé', changes[recent.HUB])
        item = json.loads(changes[recent.CATALOG])['articles'][0]
        self.assertEqual(item['datePublished'], '2026-01-01')

    def test_undated_noindex_and_unregistered_pages_are_not_recent(self):
        self.assertIsNone(recent.record(self.root, self.old, self.story(self.old, None), self.config))
        source = self.story(self.old, '2026-01-01').replace('</head>', '<meta name="robots" content="noindex,follow"></head>')
        self.assertIsNone(recent.record(self.root, self.old, source, self.config))
        self.assertIsNone(recent.record(self.root, 'commercial/index.html', source, self.config))

    def test_recent_cards_are_limited_and_have_unique_urls(self):
        extras = {}
        for i in range(10):
            path = self.city['path'] + f'/recit-{i}/index.html'
            extras[path] = self.story(path, f'2026-02-{i+1:02d}')
        changes = recent.plan(self.root, self.config, extras)
        links = self.links(changes[recent.HUB])
        self.assertEqual(len(links), 6)
        self.assertEqual(len(set(links)), 6)
        self.assertTrue(links[0].endswith('/recit-9/'))

    def test_existing_story_refresh_updates_both_cards_without_duplicates(self):
        source = self.story(self.old, '2026-01-01', title='Nouveau titre exact')
        changes = add_memory_article.prepare(self.root, 'marseille', 'ancien', source, refresh=True)
        self.assertNotIn('sitemap.xml', changes)
        self.assertIn('Nouveau titre exact', changes[recent.HUB])
        city = html.fromstring(changes[self.city['path'] + '/index.html'])
        self.assertEqual(len(city.xpath('//main//article')), 1)
        self.assertEqual(city.xpath('//main//h3/text()'), ['Nouveau titre exact'])
        self.assertIn('(1)', (self.root / recent.HUB).read_text(encoding='utf-8'))
        with self.assertRaisesRegex(AssertionError, 'preserve original'):
            add_memory_article.prepare(self.root, 'marseille', 'ancien', self.story(self.old, '2026-02-01'), refresh=True)

    def test_new_city_can_be_prepared_entirely_in_memory(self):
        config = json.loads(json.dumps(self.config))
        city = dict(self.city, id='nouvelle-ville', name='Nouvelle ville', path='Provence-Alpes-Cote-dAzur/Bouches-du-Rhone/Nouvelle-Ville', legacy=[])
        config['cities'].append(city)
        path = city['path'] + '/premier/index.html'
        extras = {city['path'] + '/index.html': '<h1>Nouvelle ville</h1>', path: self.story(path, '2026-02-01')}
        changes = recent.plan(self.root, config, extras, rebuild=True)
        self.assertEqual(self.links(changes[recent.HUB])[0], recent.route(path))
        self.assertFalse((self.root / path).exists())


if __name__ == '__main__':
    unittest.main()

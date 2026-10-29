"""Regression coverage for publication races and the explicit SEO URL scope."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import publish_generated_pages as publication
import harmonize_seo as seo


def git(root, *args):
    result = subprocess.run(['git', '-c', 'core.longpaths=true', *args], cwd=root,
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


class Workspace(unittest.TestCase):
    def setUp(self):
        self.base = TOOLS.parent / '.publication-test-tmp'
        self.base.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.base)
        self.root = Path(self.temp.name).resolve()
        self.assertTrue(self.root.is_relative_to(self.base.resolve()))

    def tearDown(self):
        # Cleanup stays inside the dedicated, resolved test workspace.
        self.assertTrue(self.root.is_relative_to(self.base.resolve()))
        self.temp.cleanup()

    def fixture(self, name):
        folder = self.root / name
        folder.mkdir()
        remote, publisher, editor = folder / 'remote.git', folder / 'publisher', folder / 'editor'
        git(folder, 'init', '--bare', '--initial-branch=main', str(remote))
        git(folder, 'clone', str(remote), str(publisher))
        git(publisher, 'config', 'user.name', 'Fixture')
        git(publisher, 'config', 'user.email', 'fixture@example.invalid')
        git(publisher, 'config', 'core.autocrlf', 'false')
        git(publisher, 'config', 'core.longpaths', 'true')
        target = publisher / publication.PORTAL
        target.parent.mkdir(parents=True)
        target.write_text('OWNER=original\nGEN=0\n', encoding='utf8')
        (publisher / 'index.html').write_text('Original home', encoding='utf8')
        (publisher / 'data.txt').write_text('1', encoding='utf8')
        git(publisher, 'add', '.')
        git(publisher, 'commit', '-m', 'Seed')
        git(publisher, 'push', '-u', 'origin', 'main')
        git(folder, 'clone', str(remote), str(editor))
        git(editor, 'config', 'user.name', 'Editor')
        git(editor, 'config', 'user.email', 'editor@example.invalid')
        git(editor, 'config', 'core.autocrlf', 'false')
        git(editor, 'config', 'core.longpaths', 'true')
        return remote, publisher, editor

    def quiet_publish(self, publisher, mode, prepare, attempts=3):
        with patch.object(publication, 'prepare', prepare), contextlib.redirect_stdout(io.StringIO()):
            return publication.publish(publisher, mode, attempts)


class PublicationTests(Workspace):
    def test_concurrent_same_page_and_home_edits_survive_in_both_modes(self):
        for mode in ('immobilier', 'seo'):
            with self.subTest(mode=mode):
                remote, publisher, editor = self.fixture(mode)
                calls = []

                def prepare(root, selected_mode):
                    calls.append(selected_mode)
                    target = root / publication.PORTAL
                    text = re.sub(r'GEN=\d+', 'GEN=' + (root / 'data.txt').read_text(),
                                  target.read_text())
                    target.write_text(text, encoding='utf8')
                    if mode == 'seo':
                        git(root, 'add', publication.PORTAL)
                    if len(calls) == 1:
                        # A real second clone publishes after our fetch, before our push.
                        (editor / publication.PORTAL).write_text('OWNER=editor\nGEN=0\n', encoding='utf8')
                        (editor / 'index.html').write_text('New home from editor', encoding='utf8')
                        (editor / 'data.txt').write_text('2', encoding='utf8')
                        git(editor, 'add', '.')
                        git(editor, 'commit', '-m', 'Concurrent editorial changes')
                        git(editor, 'push', 'origin', 'main')

                self.assertTrue(self.quiet_publish(publisher, mode, prepare))
                self.assertEqual(calls, [mode, mode])
                self.assertEqual(git(remote, 'show', 'main:' + publication.PORTAL), 'OWNER=editor\nGEN=2')
                self.assertEqual(git(remote, 'show', 'main:index.html'), 'New home from editor')
                self.assertEqual(git(remote, 'diff-tree', '--no-commit-id', '--name-only', '-r', 'main'), publication.PORTAL)

    def test_no_change_does_not_create_a_commit(self):
        remote, publisher, _ = self.fixture('noop')
        before = git(remote, 'rev-parse', 'main')
        self.assertFalse(self.quiet_publish(publisher, 'immobilier', lambda root, mode: None))
        self.assertEqual(git(remote, 'rev-parse', 'main'), before)

    def test_dirty_checkout_is_rejected_without_discarding_user_work(self):
        remote, publisher, _ = self.fixture('dirty')
        before = git(remote, 'rev-parse', 'main')
        (publisher / 'index.html').write_text('Uncommitted user work', encoding='utf8')
        with self.assertRaisesRegex(RuntimeError, 'existing tracked changes'):
            self.quiet_publish(publisher, 'immobilier', lambda root, mode: None)
        self.assertEqual((publisher / 'index.html').read_text(), 'Uncommitted user work')
        self.assertEqual(git(remote, 'rev-parse', 'main'), before)

    def test_immobilier_refuses_an_unrelated_home_change(self):
        remote, publisher, _ = self.fixture('scope')
        before = git(remote, 'rev-parse', 'main')
        def prepare(root, mode):
            (root / 'index.html').write_text('Accidental broad SEO output', encoding='utf8')
            (root / publication.PORTAL).write_text('Changed portal', encoding='utf8')
        with self.assertRaisesRegex(RuntimeError, 'outside its portal'):
            self.quiet_publish(publisher, 'immobilier', prepare)
        self.assertEqual(git(remote, 'rev-parse', 'main'), before)

    def test_repeated_races_stop_without_overwriting_the_remote(self):
        remote, publisher, editor = self.fixture('exhausted')
        calls = []
        def prepare(root, mode):
            calls.append(1)
            (root / publication.PORTAL).write_text('Our generated output', encoding='utf8')
            (editor / 'index.html').write_text('Editor version ' + str(len(calls)), encoding='utf8')
            git(editor, 'add', 'index.html')
            git(editor, 'commit', '-m', 'Editor update')
            git(editor, 'push', 'origin', 'main')
        with self.assertRaisesRegex(RuntimeError, 'after 3 attempts'):
            self.quiet_publish(publisher, 'immobilier', prepare)
        self.assertEqual(len(calls), 3)
        self.assertEqual(git(remote, 'show', 'main:' + publication.PORTAL), 'OWNER=original\nGEN=0')
        self.assertEqual(git(remote, 'show', 'main:index.html'), 'Editor version 3')


class SeoScopeTests(Workspace):
    def setUp(self):
        super().setUp()
        self.repo = self.root / 'seo'
        (self.repo / 'tools').mkdir(parents=True)
        self.urls = ['https://www.vivreanyons.fr/one/', 'https://www.vivreanyons.fr/two/']
        (self.repo / 'tools/seo-policy.json').write_text(json.dumps({
            'scope': 'global-approved', 'pilot_urls': [self.urls[1]]}), encoding='utf8')
        (self.repo / 'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
            ''.join('<url><loc>' + url + '</loc></url>' for url in self.urls) + '</urlset>', encoding='utf8')
        (self.repo / 'tools/duplicate-canonical-map.json').write_text('{"pairs":[]}', encoding='utf8')
        (self.repo / 'tools/memory-cities.json').write_text('{"cities":[]}', encoding='utf8')
        for slug, url in zip(('one', 'two'), self.urls):
            folder = self.repo / slug
            folder.mkdir()
            (folder / 'index.html').write_text('<!doctype html><html><head><title>' + slug +
                '</title><meta name="description" content="Editorial description"><link rel="canonical" href="' +
                url + '"></head><body><article class="feature-story"><h1>' + slug +
                '</h1><p>Original editorial content and photograph.</p></article></body></html>', encoding='utf8')

    def run_seo(self, *args):
        with patch.object(seo, 'ROOT', self.repo), patch.object(sys, 'argv', ['harmonize_seo', *args]), patch('consolidate_duplicate_urls.install', return_value=[]), contextlib.redirect_stdout(io.StringIO()):
            seo.main()

    def text(self, slug):
        return (self.repo / slug / 'index.html').read_text(encoding='utf8')

    def test_explicit_url_preserves_every_other_page_and_is_idempotent(self):
        other = self.text('two')
        body = self.text('one').split('</head>')[1]
        self.run_seo('--url', self.urls[0], '--apply')
        self.assertEqual(self.text('two'), other)
        self.assertEqual(self.text('one').split('</head>')[1], body)
        self.assertIn('og:title', self.text('one'))
        first = self.text('one')
        self.run_seo('--url', self.urls[0], '--check')
        self.assertEqual(self.text('one'), first)

    def test_default_pilot_selection_is_unchanged(self):
        one = self.text('one')
        self.run_seo('--apply')
        self.assertEqual(self.text('one'), one)
        self.assertIn('og:title', self.text('two'))

    def test_global_selection_is_unchanged(self):
        self.run_seo('--all', '--apply')
        for slug in ('one', 'two'):
            self.assertIn('og:title', self.text(slug))

    def test_unknown_url_fails_before_writing(self):
        before = [self.text(slug) for slug in ('one', 'two')]
        with self.assertRaisesRegex(ValueError, 'not published'):
            self.run_seo('--url', 'https://www.vivreanyons.fr/missing/', '--apply')
        self.assertEqual(before, [self.text(slug) for slug in ('one', 'two')])

    def test_global_and_explicit_scopes_cannot_be_combined(self):
        with self.assertRaises(SystemExit):
            self.run_seo('--all', '--url', self.urls[0], '--apply')


if __name__ == '__main__':
    unittest.main()

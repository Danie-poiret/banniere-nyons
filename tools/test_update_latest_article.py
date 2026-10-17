"""The homepage must remain local even when newer outside articles are published."""
import json
from pathlib import Path
import tempfile
import unittest
from update_latest_article import is_nyons_article, update


class NyonsHomepageTest(unittest.TestCase):
    def test_article_subject(self):
        examples = [
            ('/randonnee-nyons/sentier-vignoble-nyonsais/', 'Sentier du vignoble nyonsais : balade de 3 km', True),
            ('/Histoire-Geo/farceurs-quartier-pont-nyons/', 'Quartier du Pont à Nyons : les farces d’autrefois', True),
            ('/infos-pratiques-nyons/emploi-nyons/', 'Emploi à Nyons : offres et conseils', True),
            ('/Provence-Alpes-Cote-dAzur/Bouches-du-Rhone/Marseille/plages-prado-marseille-histoire/', 'Plages du Prado à Marseille', False),
            ('/Auvergne-Rhone-Alpes/Rhone/horloge-guignols-charvet-lyon/', 'Horloge aux Guignols de Lyon | Vivre à Nyons', False),
            ('/Provence-Alpes-Cote-dAzur/Vaucluse/Epicerie-Parisienne-Avignon/', 'Épicerie Parisienne à Avignon', False),
            ('/restaurants-autour-nyons/lou-cafetoun-curnier/', 'Lou Cafétoun à Curnier : spécialités près de Nyons', False),
            ('/restaurants-de-nyons/restaurant-curnier/', 'Un restaurant à Curnier près de Nyons', False),
            ('/souvenirs-lyon/', 'Souvenirs de Lyon | Vivre à Nyons', False),
            ('/a-faire-autour-de-Nyons/Vinsobres/', 'Vinsobres, autour de Nyons', False),
        ]
        for path, title, expected in examples:
            with self.subTest(path=path):
                self.assertEqual(is_nyons_article(path, title), expected)

    def test_more_recent_outside_articles_cannot_enter_the_homepage(self):
        test_parent=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(dir=test_parent) as directory:
            root=Path(directory)
            assert root.resolve().is_relative_to(test_parent)
            (root/'tools').mkdir()
            outside='/Provence-Alpes-Cote-dAzur/Bouches-du-Rhone/Marseille/futur-article/'
            (root/'tools/home-editorial-updates.json').write_text(json.dumps({'paths':[outside]}),encoding='utf-8')
            before='<header>Conserver</header><!-- HOME_LATEST_START -->Ancien bloc<!-- HOME_LATEST_END --><footer>Conserver</footer>'
            (root/'index.html').write_text(before,encoding='utf-8')
            paths=[]
            for n in range(6):
                path=f'/Histoire-Geo/nyons-souvenir-{n}/';paths.append(path)
                self.write_article(root,path,f'Souvenir {n} de Nyons',f'2026-10-{10+n:02d}')
            paths.append(outside)
            self.write_article(root,outside,'Le nouvel article de Marseille','2026-12-31')
            (root/'sitemap.xml').write_text('<urlset>'+''.join('<url><loc>https://www.vivreanyons.fr'+p+'</loc></url>' for p in paths)+'</urlset>',encoding='utf-8')
            # The production reader expects the standard namespace.
            text=(root/'sitemap.xml').read_text(encoding='utf-8').replace('<urlset>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
            (root/'sitemap.xml').write_text(text,encoding='utf-8')
            update(root)
            result=(root/'index.html').read_text(encoding='utf-8')
            self.assertEqual(result.count('class="home-latest-card"'),5)
            self.assertNotIn(outside,result)
            self.assertNotIn('nyons-souvenir-0/',result)
            for n in range(1,6):self.assertIn(f'/Histoire-Geo/nyons-souvenir-{n}/',result)
            self.assertTrue(result.startswith('<header>Conserver</header>'))
            self.assertTrue(result.endswith('<footer>Conserver</footer>'))
            update(root)
            self.assertEqual((root/'index.html').read_text(encoding='utf-8'),result)

    @staticmethod
    def write_article(root,path,title,date):
        file=root/path.strip('/')/'index.html';file.parent.mkdir(parents=True)
        item={'@type':'Article','headline':title,'description':'Une histoire locale.','datePublished':date,'dateModified':date,'image':'/assets/local.webp'}
        file.write_text('<img src="/assets/local.webp" alt="Photo locale"><script type="application/ld+json">'+json.dumps(item)+'</script>',encoding='utf-8')


if __name__=='__main__':unittest.main()

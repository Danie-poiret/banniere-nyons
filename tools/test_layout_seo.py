"""The CLS preparation must not change editorial image or summary selection."""
import unittest
from harmonize_seo import Head, excerpt, optimize, card_items
from update_latest_article import Page


class LayoutSEO(unittest.TestCase):
    def test_homepage_schema_order_survives_visual_reordering(self):
        site='https://www.vivreanyons.fr/'
        latest='<!-- HOME_LATEST_START --><article class="home-latest-card"><a href="/article/">Article</a></article><!-- HOME_LATEST_END -->'
        season='<!-- HOME_SEASON_START --><article class="home-season-card"><a href="/saison/">Saison</a></article><!-- HOME_SEASON_END -->'
        catalog={site+'article/':'<title>Article local</title>',site+'saison/':'<title>Idée de saison</title>'}
        before=card_items(latest+season,site,catalog)
        after=card_items(season+latest,site,catalog)
        self.assertEqual(after,before)
        self.assertEqual([x['item']['url'] for x in after],[site+'article/',site+'saison/'])
        # Other collections retain their original DOM-driven selection order.
        self.assertNotEqual(card_items(season+latest,site+'rubrique/',catalog),before)

    def test_partner_cards_do_not_change_editorial_analysis(self):
        url='https://www.vivreanyons.fr/exemple/'
        source='''<!doctype html><html><head><title>Histoire de Nyons</title>
<link rel="canonical" href="https://www.vivreanyons.fr/exemple/">
<meta name="description" content="Un véritable article sur les souvenirs et photographies de Nyons.">
</head><body><main><h1>Histoire de Nyons</h1>
<p>Ce récit conserve ses souvenirs, ses photographies et ses sources historiques originales.</p>
<img src="/photo-article.jpg" width="960" height="676" alt="Photo historique de Nyons">
</main></body></html>'''
        partner='''<!-- nyons-layout-partners:start --><div data-nyons-partner-cards data-nosnippet>
<aside><img src="/partenaire.jpg" width="88" height="88" alt="Partenaire"><p>Texte du partenaire.</p></aside>
</div><!-- nyons-layout-partners:end -->'''
        prepared=source.replace('<main>','<main>'+partner)
        self.assertEqual(Head(source).images,Head(prepared).images)
        self.assertEqual(Page(source).images,Page(prepared).images)
        self.assertEqual(excerpt(source,'Histoire de Nyons'),excerpt(prepared,'Histoire de Nyons'))
        before,_=optimize(source,url,{'kinds':{url:'article'}},{url:source})
        after,_=optimize(prepared,url,{'kinds':{url:'article'}},{url:prepared})
        self.assertEqual(before.split('</head>')[0],after.split('</head>')[0])
        self.assertIn('content="https://www.vivreanyons.fr/photo-article.jpg"',after)
        self.assertNotIn('content="https://www.vivreanyons.fr/partenaire.jpg"',after)

    def test_an_article_using_the_same_photo_keeps_its_own_dimensions(self):
        source='<main><img src="/shared.jpg" width="960" height="676" alt="Article"></main>'
        prepared='<!-- nyons-layout-partners:start --><aside data-nyons-partner-cards><img src="/shared.jpg" width="88" height="88" alt="Partenaire"></aside><!-- nyons-layout-partners:end -->'+source
        self.assertEqual(Page(prepared).images[0]['width'],'960')
        self.assertEqual(Head(prepared).images,Head(source).images)


if __name__=='__main__':unittest.main()

import copy
import json
import unittest
from editorial_identity import harmonize, SCRIPTS, PERSON, ORG


class EditorialIdentityTests(unittest.TestCase):
    def page(self, data):
        return '<html><head><script type="application/ld+json">' + json.dumps(data) + '</script></head><body><p>Texte inchangé</p></body></html>'

    def test_preserves_editorial_facts_and_other_author(self):
        article = {'@type': 'Article', 'headline': 'Un récit', 'author': {'@type': 'Person', 'name': 'Autre auteur'}, 'datePublished': '2020-01-02', 'dateModified': '2021-02-03', 'image': '/photo.jpg', 'publisher': {'@type': 'Organization', 'name': 'Vivre à Nyons', 'logo': '/logo.png'}}
        after = harmonize(self.page(article))
        result = json.loads(SCRIPTS.search(after)[1])
        self.assertEqual(result['author'], article['author'])
        for key in ('datePublished', 'dateModified', 'image', 'headline'):
            self.assertEqual(result[key], article[key])
        self.assertEqual(result['publisher']['logo'], '/logo.png')
        self.assertEqual(result['publisher']['@id'], ORG)

    def test_shared_person_reference_and_idempotence(self):
        page = self.page({'@type': 'BlogPosting', 'author': {'@type': 'Person', 'name': 'Papy Chris'}, 'publisher': {'@id': ORG}})
        after = harmonize(page)
        article = json.loads(SCRIPTS.search(after)[1])
        self.assertEqual(article['author']['@id'], PERSON)
        self.assertEqual(after, harmonize(after))
        self.assertEqual(SCRIPTS.sub('', after), SCRIPTS.sub('', page))

    def test_invalid_schema_is_not_silently_replaced(self):
        with self.assertRaises(json.JSONDecodeError):
            harmonize('<head><script type="application/ld+json">{bad}</script></head>')


if __name__ == '__main__':
    unittest.main()

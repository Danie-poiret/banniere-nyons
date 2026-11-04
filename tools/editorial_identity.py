"""Keep public JSON-LD authors and publisher attached to stable site identities."""
import copy
import json
import re
import unicodedata

SITE = 'https://www.vivreanyons.fr/'
ORG = SITE + '#organization'
PERSON = SITE + '#papy-chris'
WEBSITE = SITE + '#website'
MARKER = 'data-nyons-editorial-identity'
SCRIPTS = re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
IDENTITIES = [
    {'@type': 'Organization', '@id': ORG, 'name': 'Vivre à Nyons', 'url': SITE,
     'description': 'Guide local indépendant de Papy Chris consacré à Nyons et à la Drôme provençale : tourisme, patrimoine, terroir, hébergements, restaurants et vie locale.',
     'email': 'contact@vivreanyons.fr',
     'contactPoint': {'@type': 'ContactPoint', 'email': 'contact@vivreanyons.fr', 'contactType': 'Contact éditorial', 'availableLanguage': 'fr'}},
    {'@type': 'Person', '@id': PERSON, 'name': 'Papy Chris', 'url': SITE,
     'description': 'Auteur du guide local Vivre à Nyons, consacré à Nyons, au patrimoine, au terroir et à la vie locale.'},
    {'@type': 'WebSite', '@id': WEBSITE, 'name': 'Vivre à Nyons', 'url': SITE,
     'inLanguage': 'fr', 'publisher': {'@id': ORG}, 'creator': {'@id': PERSON}},
]

def normal(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value)).lower() if c.isalnum())

def harmonize(source):
    """Only change JSON-LD; keep unrelated people, businesses, dates and HTML."""
    before = source
    source = re.sub(r'<script\b[^>]*' + MARKER + r'[^>]*>.*?</script>', '', source, flags=re.S)
    defined = set()

    def walk(node):
        if isinstance(node, list):
            for child in node:
                walk(child)
            return
        if not isinstance(node, dict):
            return
        types = node.get('@type', [])
        types = {types} if isinstance(types, str) else set(types)
        name = normal(node.get('name', ''))
        own_org = name in {'vivreanyons', 'vivreanyonsfr'}
        own_person = name == 'papychris'
        if 'Organization' in types and (own_org or node.get('@id') == ORG):
            node['@id'] = ORG
            for key, value in IDENTITIES[0].items():
                node.setdefault(key, copy.deepcopy(value))
        if 'Person' in types and (own_person or node.get('@id') == PERSON):
            node['@id'] = PERSON
            for key, value in IDENTITIES[1].items():
                node.setdefault(key, copy.deepcopy(value))
        if 'WebSite' in types and (own_org or node.get('@id') == WEBSITE or node.get('url') == SITE):
            node['@id'] = WEBSITE
            node['publisher'] = {'@id': ORG}
            node['creator'] = {'@id': PERSON}
        if types.intersection({'Article', 'BlogPosting', 'NewsArticle'}):
            node.setdefault('author', {'@id': PERSON})
        if types.intersection({'Article', 'BlogPosting', 'NewsArticle', 'WebPage', 'CollectionPage', 'AboutPage', 'ContactPage', 'FAQPage'}):
            publisher = node.get('publisher')
            if publisher is None or (isinstance(publisher, str) and normal(publisher) in {'vivreanyons', 'vivreanyonsfr'}):
                node['publisher'] = {'@id': ORG}
            elif isinstance(publisher, dict) and normal(publisher.get('name', '')) in {'vivreanyons', 'vivreanyonsfr'}:
                publisher['@id'] = ORG
                publisher.setdefault('@type', 'Organization')
        if 'author' in node:
            author = node['author']
            if isinstance(author, str) and normal(author) == 'papychris':
                node['author'] = {'@id': PERSON}
            elif isinstance(author, dict) and normal(author.get('name', '')) == 'papychris':
                author['@id'] = PERSON
        for value in list(node.values()):
            walk(value)
        if node.get('@id') in {ORG, PERSON, WEBSITE} and node.get('@type'):
            defined.add(node['@id'])

    def update(match):
        data = json.loads(match[1])
        original = copy.deepcopy(data)
        walk(data)
        if original == data:
            return match[0]
        return match[0][:match.start(1)-match.start()] + json.dumps(data, ensure_ascii=False).replace('</', r'<\/') + match[0][match.end(1)-match.start():]

    source = SCRIPTS.sub(update, source)
    missing = [copy.deepcopy(item) for item in IDENTITIES if item['@id'] not in defined]
    if missing:
        block = '<script type="application/ld+json" ' + MARKER + '>' + json.dumps({'@context': 'https://schema.org', '@graph': missing}, ensure_ascii=False) + '</script>'
        if '</head>' not in source:
            raise ValueError('Missing head')
        source = source.replace('</head>', block + '</head>', 1)
    assert SCRIPTS.sub('', source) == SCRIPTS.sub('', before), 'Non-schema HTML changed'
    return source

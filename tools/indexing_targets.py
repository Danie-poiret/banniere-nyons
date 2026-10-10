"""Stable URLs for the nine pages reported as duplicates in Search Console."""
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote

SITE = 'https://www.vivreanyons.fr/'
PREFIXES = ('', 'vivreanyons-test/', 'banniere-nyons/vivreanyons-test/')
SLUGS = (
    'ou-dormir-a-nyons/capfun-de-nyons/',
    'que-faire-nyons/spots-baignades-nyons/',
    'restaurants-de-nyons/Restaurant-thai/',
    'restaurants-de-nyons/berli-nyons/',
    'que-faire-nyons/nyons-week-end/',
    'que-faire-nyons/les-vieux-moulins/',
    'restaurants-de-nyons/Restaurant-alicoque-Nyons/',
    'a-faire-autour-de-Nyons/se-baigner-aubres/',
    'a-faire-autour-de-Nyons/village-de-venterol/',
)
TARGETS = {s.rstrip('/').lower(): s for s in SLUGS}

def canonical_link(raw, relative_file):
    """Normalize only links to known targets; preserve query and fragment."""
    base = SITE + relative_file.removesuffix('index.html')
    resolved = urlsplit(urljoin(base, raw))
    if resolved.hostname not in {'www.vivreanyons.fr', 'vivreanyons.fr'}:
        return raw
    path = unquote(resolved.path).lstrip('/')
    prefix = next(p for p in reversed(PREFIXES) if path.startswith(p))
    key = path[len(prefix):].removesuffix('index.html').rstrip('/').lower()
    if key not in TARGETS:
        return raw
    expected = '/' + prefix + TARGETS[key]
    if resolved.path == expected and (resolved.scheme, resolved.hostname) == ('https', 'www.vivreanyons.fr'):
        return raw
    if raw.startswith(('http://', 'https://', '//')):
        return urlunsplit(('https', 'www.vivreanyons.fr', expected, resolved.query, resolved.fragment))
    return urlunsplit(('', '', expected, resolved.query, resolved.fragment))

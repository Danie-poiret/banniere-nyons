"""Consolidate the Venterol duplicate while keeping all existing incoming URLs usable."""
import html
import json
import os
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
OLD = "que-faire-autour-de-nyons/village-de-venterol/"
NEW = "a-faire-autour-de-Nyons/village-de-venterol/"
SITE = "https://www.vivreanyons.fr"
PREFIXES = ("", "vivreanyons-test/", "banniere-nyons/vivreanyons-test/")
CANONICAL = SITE + "/" + NEW
ATTR = re.compile(r"""(?P<lead>\b(?:href|action)\s*=\s*["'])(?P<url>[^"']+)(?P<end>["'])""", re.I)
URL_NODE = re.compile(r"<url>.*?</url>", re.S)
ARTICLE = re.compile(r'<article\b[^>]*class=["\'][^"\']*\bfeature-story\b[^"\']*["\'][^>]*>.*?</article>', re.S)
GALLERY = re.compile(r'<aside\b[^>]*class=["\'][^"\']*\bfeature-media\b[^"\']*["\'][^>]*>.*?</aside>', re.S)
target_pages = {}
for prefix in PREFIXES:
    path = ROOT / (prefix + NEW + "index.html")
    if not path.is_file():
        raise RuntimeError("Missing destination: " + str(path))
    source = path.read_text(encoding="utf-8")
    article = ARTICLE.search(source)
    gallery = GALLERY.search(source)
    if not article or not gallery:
        raise RuntimeError("Destination article or photos missing")
    target_pages[path] = {
        "source": source,
        "article": article.group(),
        "gallery": gallery.group(),
        "canonical": re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>', source).group(),
        "published": re.findall(r'"datePublished"\s*:\s*"([^"]+)"', source),
    }

def route(url):
    parsed = urlsplit(url)
    if parsed.hostname and parsed.hostname not in {"www.vivreanyons.fr", "vivreanyons.fr"}:
        return None
    path = parsed.path.lstrip("/")
    if path.endswith("index.html"):
        path = path[:-len("index.html")]
    for prefix in reversed(PREFIXES):
        if path.rstrip("/") == (prefix + OLD).rstrip("/"):
            return prefix
    return None

def rewrite_attribute(match, file):
    raw = html.unescape(match.group("url"))
    base = SITE + "/" + file.parent.relative_to(ROOT).as_posix() + "/"
    resolved = urlsplit(urljoin(base, raw))
    prefix = route(urlunsplit(resolved))
    if prefix is None:
        return match.group()
    path = "/" + prefix + NEW
    replacement = urlunsplit((resolved.scheme, resolved.netloc, path, resolved.query, resolved.fragment))
    if not raw.startswith(("http://", "https://", "//")):
        replacement = urlunsplit(("", "", path, resolved.query, resolved.fragment))
    return match.group("lead") + html.escape(replacement, quote=True) + match.group("end")

changed = []
links = 0
cards_removed = 0
for directory, subdirs, files in os.walk(ROOT):
    subdirs[:] = [name for name in subdirs if name not in {".git", "node_modules", ".venv"}]
    for name in files:
        if not name.endswith(".html"):
            continue
        file = Path(directory) / name
        relative = file.relative_to(ROOT).as_posix()
        if relative in {prefix + OLD + "index.html" for prefix in PREFIXES}:
            continue
        source = file.read_text(encoding="utf-8")
        def replace_attr(match):
            global links
            result = rewrite_attribute(match, file)
            if result != match.group():
                links += 1
            return result
        updated = ATTR.sub(replace_attr, source)
        seen = set()
        def unique_card(match):
            global cards_removed
            card = match.group()
            destinations = re.findall(r'href=["\']([^"\']+)["\']', card)
            destination = next((urlsplit(html.unescape(url)).path.rstrip("/") for url in destinations if urlsplit(html.unescape(url)).path.rstrip("/").endswith("/" + NEW.rstrip("/"))), None)
            if destination is None:
                return card
            if destination in seen:
                cards_removed += 1
                return ""
            seen.add(destination)
            return card
        updated = re.sub(r'<article\b[^>]*class=["\']card["\'][^>]*>.*?</article>', unique_card, updated, flags=re.S)
        if updated != source:
            file.write_text(updated, encoding="utf-8")
            changed.append(relative)

redirects = []
for prefix in PREFIXES:
    alias = ROOT / (prefix + OLD + "index.html")
    if not alias.is_file():
        raise RuntimeError("Missing old address: " + str(alias))
    source = alias.read_text(encoding="utf-8")
    destination = "/" + prefix + NEW
    robots = "index,follow" if not prefix else "noindex,nofollow"
    header = re.search(r"<header\b.*?</header>", source, re.S)
    footer = re.search(r"<footer\b.*?</footer>", source, re.S)
    if not header or not footer:
        raise RuntimeError("Existing navigation/footer missing: " + str(alias))
    scripts = "\n".join(re.findall(r"""<script\b[^>]*src=["'][^"']+["'][^>]*>.*?</script>""", source, re.S))
    result = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="{robots}">
<meta http-equiv="refresh" content="0; url={destination}">
<title>Venterol : la fiche à découvrir</title>
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="/{prefix}assets/style.css?v=privacy-20261002-v1">
</head>
<body>
{header}
<main><div class="wrap content"><h1>Venterol</h1><p>La fiche de Venterol se trouve à cette adresse :</p><p><a href="{destination}">Découvrir Venterol : ruelles, campanile et rue du Bout du Monde</a></p></div></main>
{footer}
{scripts}
</body>
</html>
""".format(robots=robots, destination=html.escape(destination, quote=True), canonical=CANONICAL, prefix=prefix, header=header.group(), footer=footer.group(), scripts=scripts)
    if result != source:
        alias.write_text(result, encoding="utf-8")
        changed.append(alias.relative_to(ROOT).as_posix())
    redirects.append(alias.relative_to(ROOT).as_posix())

sitemap_removed = 0
for file in ROOT.rglob("sitemap.xml"):
    if ".git" in file.parts:
        continue
    source = file.read_text(encoding="utf-8")
    def sitemap_node(match):
        global sitemap_removed
        node = match.group()
        location = re.search(r"<loc>(.*?)</loc>", node, re.S)
        if location and route(html.unescape(location.group(1))) is not None:
            sitemap_removed += 1
            return ""
        return node
    updated = URL_NODE.sub(sitemap_node, source)
    if updated != source:
        file.write_text(updated, encoding="utf-8")
        changed.append(file.relative_to(ROOT).as_posix())

for path, before in target_pages.items():
    source = path.read_text(encoding="utf-8")
    if ARTICLE.search(source).group() != before["article"]:
        raise RuntimeError("Main article content changed unexpectedly")
    if GALLERY.search(source).group() != before["gallery"]:
        raise RuntimeError("Main article photos changed unexpectedly")
    if re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>', source).group() != before["canonical"]:
        raise RuntimeError("Destination canonical changed")
    if re.findall(r'"datePublished"\s*:\s*"([^"]+)"', source) != before["published"]:
        raise RuntimeError("Publication date changed")

sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
if sitemap.count("<loc>" + CANONICAL + "</loc>") != 1:
    raise RuntimeError("Destination must appear exactly once in sitemap")
if any(route(html.unescape(url)) is not None for url in re.findall(r"<loc>(.*?)</loc>", sitemap)):
    raise RuntimeError("Old URL remains in sitemap")

for directory, subdirs, files in os.walk(ROOT):
    subdirs[:] = [name for name in subdirs if name not in {".git", "node_modules", ".venv"}]
    for name in files:
        if not name.endswith(".html"):
            continue
        file = Path(directory) / name
        if file.relative_to(ROOT).as_posix() in redirects:
            continue
        source = file.read_text(encoding="utf-8")
        for match in ATTR.finditer(source):
            if rewrite_attribute(match, file) != match.group():
                raise RuntimeError("Unconsolidated link: " + str(file))

audit = ROOT / "tools/venterol-canonical-audit.json"
if changed or not audit.is_file():
    audit.write_text(json.dumps({
        "canonical": CANONICAL,
        "date": "2026-10-07",
        "redirectType": "HTML meta refresh 0 seconds, treated as permanent by Google",
        "sourcePath": "/" + OLD,
        "redirectPages": redirects,
        "rewrittenLinks": links,
        "duplicateCardsRemoved": cards_removed,
        "sitemapEntriesRemoved": sitemap_removed,
        "changedFiles": sorted(set(changed)),
        "mainArticleAndPhotosPreserved": True,
        "mainCanonicalAndPublicationDatesPreserved": True,
        "reference": "https://developers.google.com/search/docs/crawling-indexing/301-redirects"
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Venterol consolidation: {} changed files; {} rewritten links; {} duplicate cards removed; {} sitemap entries removed; main article and photos preserved.".format(len(set(changed)), links, cards_removed, sitemap_removed))

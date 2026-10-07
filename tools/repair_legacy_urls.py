"""Restore two malformed legacy URLs; keep unknown technical URLs as real 404s."""
import html
import json
import os
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://www.vivreanyons.fr"
PREFIXES = ("", "vivreanyons-test/", "banniere-nyons/vivreanyons-test/")
ROUTES = {
    "Provence-Alpes-Cote-dAzur/Auvergne-Rhone-Alpes/Drome/Piscine-de-Pierrelatte/": "Auvergne-Rhone-Alpes/Drome/Piscine-de-Pierrelatte/",
    "evenements-/": "evenements-nyons/",
}
ATTR = re.compile(r"""(?P<lead>\bhref\s*=\s*["'])(?P<url>[^"']+)(?P<end>["'])""", re.I)
before = {}
for prefix in PREFIXES:
    for target in ROUTES.values():
        path = ROOT / (prefix + target + "index.html")
        if not path.is_file():
            raise RuntimeError("Missing replacement page: " + str(path))
        before[path] = path.read_text(encoding="utf-8")

def route(url):
    parsed = urlsplit(url)
    if parsed.hostname and parsed.hostname not in {"vivreanyons.fr", "www.vivreanyons.fr"}:
        return None
    path = parsed.path.lstrip("/")
    if path.endswith("index.html"):
        path = path[:-10]
    for prefix in reversed(PREFIXES):
        for old, target in ROUTES.items():
            if path.rstrip("/") == (prefix + old).rstrip("/"):
                return prefix, target
    return None

changed, technical_links = [], []
rewritten = 0
for directory, subdirs, filenames in os.walk(ROOT):
    subdirs[:] = [name for name in subdirs if name not in {".git", "node_modules", ".venv"}]
    for name in filenames:
        if not name.endswith(".html"):
            continue
        file = Path(directory) / name
        source = file.read_text(encoding="utf-8")
        def change(match):
            global rewritten
            raw = html.unescape(match.group("url"))
            base = SITE + "/" + file.parent.relative_to(ROOT).as_posix() + "/"
            resolved = urlsplit(urljoin(base, raw))
            if resolved.path.rstrip("/").endswith("/naLogImpressions"):
                technical_links.append(file.relative_to(ROOT).as_posix())
            item = route(urlunsplit(resolved))
            if item is None:
                return match.group()
            prefix, target = item
            destination = "/" + prefix + target
            parts = ("", "", destination, resolved.query, resolved.fragment)
            if raw.startswith(("http://", "https://", "//")):
                parts = (resolved.scheme, resolved.netloc, destination, resolved.query, resolved.fragment)
            rewritten += 1
            return match.group("lead") + html.escape(urlunsplit(parts), quote=True) + match.group("end")
        updated = ATTR.sub(change, source)
        if updated != source:
            file.write_text(updated, encoding="utf-8")
            changed.append(file.relative_to(ROOT).as_posix())

for prefix in PREFIXES:
    for old, target in ROUTES.items():
        file = ROOT / (prefix + old + "index.html")
        source = before[ROOT / (prefix + target + "index.html")]
        header = re.search(r"<header\b.*?</header>", source, re.S)
        footer = re.search(r"<footer\b.*?</footer>", source, re.S)
        title = re.search(r"<title>(.*?)</title>", source, re.S)
        if not header or not footer or not title:
            raise RuntimeError("Replacement page navigation/title missing")
        destination = "/" + prefix + target
        canonical = SITE + "/" + target
        robots = "index,follow" if not prefix else "noindex,nofollow"
        scripts = "\n".join(re.findall(r"""<script\b[^>]*src=["'][^"']+["'][^>]*>.*?</script>""", source, re.S))
        result = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="{robots}">
<meta http-equiv="refresh" content="0; url={destination}">
<title>{title}</title><link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="/{prefix}assets/style.css?v=privacy-20261002-v1">
</head><body>{header}
<main><div class="wrap content"><h1>{title}</h1><p><a href="{destination}">Continuer vers la page</a></p></div></main>
{footer}{scripts}</body></html>
""".format(robots=robots, destination=html.escape(destination, quote=True), canonical=canonical, title=title.group(1), prefix=prefix, header=header.group(), footer=footer.group(), scripts=scripts)
        if not file.is_file() or file.read_text(encoding="utf-8") != result:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(result, encoding="utf-8")
            changed.append(file.relative_to(ROOT).as_posix())

removed = 0
for file in ROOT.rglob("sitemap.xml"):
    if ".git" in file.parts:
        continue
    source = file.read_text(encoding="utf-8")
    def node(match):
        global removed
        location = re.search(r"<loc>(.*?)</loc>", match.group(), re.S)
        if location and route(html.unescape(location.group(1))) is not None:
            removed += 1
            return ""
        return match.group()
    updated = re.sub(r"<url>.*?</url>", node, source, flags=re.S)
    if updated != source:
        file.write_text(updated, encoding="utf-8")
        changed.append(file.relative_to(ROOT).as_posix())

for path, original in before.items():
    if path.read_text(encoding="utf-8") != original:
        raise RuntimeError("Existing destination changed: " + str(path))
if technical_links:
    raise RuntimeError("Unexpected links to naLogImpressions: " + repr(technical_links))

audit = ROOT / "tools/legacy-url-repair-audit.json"
if changed or not audit.is_file():
    audit.write_text(json.dumps({
        "date": "2026-10-07",
        "redirects": ROUTES,
        "redirectType": "Instant HTML meta refresh",
        "changedFiles": sorted(set(changed)),
        "linksRewritten": rewritten,
        "sitemapEntriesRemoved": removed,
        "technicalUrl": "/naLogImpressions",
        "technicalUrlReferencedBySite": False,
        "technicalUrlHandling": "No content replacement exists; preserve real 404",
        "existingDestinationPagesPreserved": True
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Legacy URL repair: {} changed files; {} rewritten links; {} sitemap entries removed; destinations preserved; no naLogImpressions links.".format(len(set(changed)), rewritten, removed))

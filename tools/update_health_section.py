"""Publish the health category without moving any existing page.

The manifest lists existing fiche URLs. Changes are limited to navigation,
category labels, category backlinks, breadcrumbs and the category indexes.
Run from the repository root; a second run makes no further changes.
"""
import html
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "tools/health-section.json").read_text(encoding="utf-8"))
SLUG = MANIFEST["categorySlug"]
TITLE = MANIFEST["title"]
CANONICAL = "https://www.vivreanyons.fr/" + SLUG
ITEMS = {item[0]: item for section in MANIFEST["sections"] for item in section["items"]}
PREFIXES = ("", "vivreanyons-test/", "banniere-nyons/vivreanyons-test/")
JSON_RE = re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S)
ARTICLE_RE = re.compile(r'(<article\b[^>]*class=["\'][^"\']*\bfeature-story\b[^"\']*["\'][^>]*>)(.*?)(</article>)', re.S)
BACK_RE = re.compile(r'<p\b[^>]*data-health-back-link[^>]*>.*?</p>\n?', re.S)

def prefix_for(path):
    relative = path.relative_to(ROOT).as_posix()
    for prefix in reversed(PREFIXES[1:]):
        if relative.startswith(prefix):
            return prefix
    return ""

def strip_tags(value):
    return html.unescape(re.sub(r"<[^>]+>", "", value))

def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)

def identities(source):
    titles = re.findall(r"<title>(.*?)</title>", source, re.S)
    headings = re.findall(r"<h1\b[^>]*>(.*?)</h1>", source, re.S)
    canonicals = re.findall(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', source)
    published = []
    for match in JSON_RE.finditer(source):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        for item in objects(value):
            kind = item.get("@type")
            if kind == "Article" or isinstance(kind, list) and "Article" in kind:
                published.append((item.get("datePublished"), item.get("mainEntityOfPage"), item.get("@id")))
    return titles, headings, canonicals, published

def update_header(source, prefix):
    href = "/" + prefix + SLUG
    def change(match):
        header = match.group(0)
        if "rubriques-menu" not in header:
            return header
        if 'data-health-nav="rubrique"' not in header:
            link = f'<a data-health-nav="rubrique" href="{href}">Santé</a>'
            pattern = r'(<div\b[^>]*class=["\'][^"\']*\brubriques-menu\b[^"\']*["\'][^>]*>)'
            header, count = re.subn(pattern, lambda found: found.group(1) + link, header, count=1)
            if count != 1:
                raise ValueError("Cannot locate the category dropdown")
        if 'data-health-nav="direct"' not in header:
            link = f'<a data-health-nav="direct" data-nyons-shortcut="sante" href="{href}">Santé</a>'
            pattern = r'(<details\b[^>]*class=["\'][^"\']*\brubriques\b[^"\']*["\'][^>]*>)'
            header, count = re.subn(pattern, lambda found: link + found.group(1), header, count=1)
            if count != 1:
                raise ValueError("Cannot locate the main category menu")
        return header
    return re.sub(r"<header\b[^>]*>.*?</header>", change, source, flags=re.S)

def update_breadcrumb(source, prefix, slug):
    page_name_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", source, re.S)
    if not page_name_match:
        raise ValueError("Missing fiche h1: " + slug)
    page_name = strip_tags(page_name_match.group(1))
    breadcrumb = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://www.vivreanyons.fr/"},
            {"@type": "ListItem", "position": 2, "name": TITLE, "item": CANONICAL},
            {"@type": "ListItem", "position": 3, "name": page_name, "item": "https://www.vivreanyons.fr/" + slug}
        ]
    }
    found_breadcrumb = False
    def change(match):
        nonlocal found_breadcrumb
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            return match.group(0)
        changed = False
        for item in objects(value):
            if item.get("@type") == "BreadcrumbList":
                found_breadcrumb = True
                if item.get("itemListElement") != breadcrumb["itemListElement"]:
                    item["itemListElement"] = breadcrumb["itemListElement"]
                    changed = True
        if not changed:
            return match.group(0)
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", r"\u003c")
        return '<script type="application/ld+json">' + payload + "</script>"
    result = JSON_RE.sub(change, source)
    if not found_breadcrumb:
        payload = {"@context": "https://schema.org", **breadcrumb}
        marker = '<script type="application/ld+json">' + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "</script>"
        if "</head>" not in result:
            raise ValueError("Missing head: " + slug)
        result = result.replace("</head>", marker + "</head>", 1)
    return result

def update_fiche(source, prefix, slug):
    result = source
    badge = "🐾 Santé des animaux" if slug.endswith(("veterinaire-nyons/", "chiens-chats-nyons/")) else "🩺 Santé à Nyons"
    hero_pattern = r'(<section\b[^>]*class=["\']hero["\'][^>]*>.*?<span\b[^>]*class=["\']badge["\'][^>]*>).*?(</span>)'
    result, count = re.subn(hero_pattern, lambda m: m.group(1) + badge + m.group(2), result, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Missing fiche category badge: " + slug)
    back = f'<p class="health-back-link" data-health-back-link><a href="/{prefix}{SLUG}">← Toutes les fiches Santé à Nyons</a></p>\n'
    match = ARTICLE_RE.search(result)
    if not match:
        raise ValueError("Missing fiche article: " + slug)
    clean_body = BACK_RE.sub("", match.group(2))
    replacement = match.group(1) + back + clean_body + match.group(3)
    result = result[:match.start()] + replacement + result[match.end():]
    after_body = ARTICLE_RE.search(result).group(2)
    if BACK_RE.sub("", after_body) != clean_body:
        raise ValueError("Fiche text changed: " + slug)
    result = update_breadcrumb(result, prefix, slug)
    return result

def add_category_card(source, prefix, homepage=False):
    if 'data-health-category="card"' in source:
        return source
    heading = "🩺 Santé à Nyons"
    summary = "Médecins, dentistes, pharmacies, urgences, hôpital, aides et santé des animaux : les fiches réunies au même endroit."
    paragraph = "<p>" + summary + "</p>"
    if homepage:
        paragraph = '<p class="home-card-copy"><span>Les contacts pour prendre soin de soi.</span><span>Médecins, pharmacies, urgences et aides…</span><span>Toutes les fiches santé au même endroit.</span></p>'
    card = f'<article class="card" data-health-category="card"><div class="kicker">Rubrique</div><h2><a class="card-title-link" href="/{prefix}{SLUG}">{heading}</a></h2>{paragraph}</article>'
    pattern = r'(<section\b[^>]*class=["\']grid["\'][^>]*>)'
    result, count = re.subn(pattern, lambda m: m.group(1) + card, source, count=1)
    if count != 1:
        raise ValueError("Missing category card grid")
    return result

def plan_updates():
    updates = {}
    menu_pages = 0
    fiche_versions = 0
    for prefix in PREFIXES:
        for slug in ITEMS:
            if not (ROOT / prefix / slug / "index.html").is_file():
                raise ValueError("Missing existing fiche: " + prefix + slug)
        if not (ROOT / prefix / SLUG / "index.html").is_file():
            raise ValueError("Missing new health category: " + prefix)
    for directory, subdirs, files in os.walk(ROOT):
        subdirs[:] = [name for name in subdirs if name not in {".git", ".github", "assets", "tools", "work", "node_modules"}]
        if "index.html" not in files:
            continue
        path = Path(directory) / "index.html"
        source = path.read_text(encoding="utf-8")
        prefix = prefix_for(path)
        relative = path.relative_to(ROOT).as_posix()
        logical = relative[len(prefix):] if prefix else relative
        slug = logical[:-len("index.html")]
        before = identities(source)
        result = update_header(source, prefix)
        if 'data-health-nav="direct"' in result:
            menu_pages += 1
        if slug in ITEMS:
            result = update_fiche(result, prefix, slug)
            fiche_versions += 1
        if logical in {"index.html", "infos-pratiques-nyons/index.html", "toutes-les-pages/index.html"}:
            result = add_category_card(result, prefix, homepage=logical == "index.html")
        if identities(result) != before:
            raise ValueError("An existing title, URL or Article identity changed: " + relative)
        if result != source:
            updates[path] = result
    if fiche_versions != len(ITEMS) * len(PREFIXES):
        raise ValueError("Not all fiche versions were categorized")
    sitemap_path = ROOT / "sitemap.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8")
    if "<loc>" + CANONICAL + "</loc>" not in sitemap:
        entry = "  <url>\n    <loc>" + CANONICAL + "</loc>\n    <lastmod>" + MANIFEST["date"] + "</lastmod>\n  </url>\n"
        sitemap = sitemap.replace("</urlset>", entry + "</urlset>", 1)
        updates[sitemap_path] = sitemap
    for prefix in PREFIXES:
        category_path = ROOT / prefix / SLUG / "index.html"
        category = updates.get(category_path, category_path.read_text(encoding="utf-8"))
        for slug in ITEMS:
            if 'href="/' + prefix + slug + '"' not in category:
                raise ValueError("Health category does not link to: " + slug)
        if "CollectionPage" not in category:
            raise ValueError("Missing category structured data")
    return updates, menu_pages, fiche_versions

def main():
    updates, menu_pages, fiche_versions = plan_updates()
    for path, source in updates.items():
        path.write_text(source, encoding="utf-8")
    again, _, _ = plan_updates()
    if again:
        raise ValueError("Health category update is not idempotent")
    print(f"Health category: {len(ITEMS)} fiches; {fiche_versions} categorized versions; {menu_pages} navigation pages; {len(updates)} updated files.")
    print("Existing fiche titles, URLs, publication dates and article texts preserved.")

if __name__ == "__main__":
    main()

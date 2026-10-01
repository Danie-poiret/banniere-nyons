#!/usr/bin/env python3
"""Importe les pages HTML Google Sites du dossier Drive dans le pilote statique.

Le script conserve le texte éditorial et les vidéos YouTube, mais retire la
navigation et les habillages Google Sites. Les photos seront ajoutées lors
d'une passe séparée, à raison d'une photo par page.
"""

from __future__ import annotations

import argparse
import html as html_std
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from lxml import html


SITE_ROOT = "/banniere-nyons/vivreanyons-test"
LIVE_ROOT = "https://www.vivreanyons.fr"

CATEGORY_SLUGS = {
    "Infos pratiques Nyons": "infos-pratiques-nyons",
    "Où dormir à Nyons ?": "ou-dormir-a-nyons",
    "Où dormir à Nyons ?": "ou-dormir-a-nyons",
    "Restaurants de Nyons": "restaurants-de-nyons",
    "Événements Nyons": "evenements-nyons",
    "Que faire à Nyons": "que-faire-nyons",
    "Produits du terroir": "produits-du-terroir",
    "Que faire autour de nyons ?": "que-faire-autour-de-nyons",
    "Histoire de Nyons en vidéo": "histoire-de-nyons-en-video",
    "Histoire Géo": "histoire-geo",
    "Questions utiles Nyons": "questions-utiles-nyons",
    "Auvergne-Rhône-Alpes": "auvergne-rhone-alpes",
    "Rhône": "rhone",
    "Drôme": "drome",
    "Provence-Alpes-Côte d'Azur": "provence-alpes-cote-dazur",
}

CATEGORY_LABELS = {
    "infos-pratiques-nyons": ("Infos pratiques à Nyons", "🧭"),
    "ou-dormir-a-nyons": ("Où dormir à Nyons", "🛏️"),
    "restaurants-de-nyons": ("Restaurants de Nyons", "🍽️"),
    "evenements-nyons": ("Événements de Nyons", "🎉"),
    "que-faire-nyons": ("Que faire à Nyons", "☀️"),
    "produits-du-terroir": ("Produits du terroir", "🫒"),
    "que-faire-autour-de-nyons": ("À découvrir autour de Nyons", "🚗"),
    "histoire-de-nyons-en-video": ("Nyons en vidéo", "🎬"),
    "histoire-geo": ("Histoire et mémoire", "🏛️"),
    "questions-utiles-nyons": ("Questions utiles sur Nyons", "❓"),
    "auvergne-rhone-alpes": ("Auvergne-Rhône-Alpes", "🗺️"),
    "auvergne-rhone-alpes/drome": ("Drôme", "🏞️"),
    "auvergne-rhone-alpes/rhone": ("Rhône et Lyon", "🏙️"),
    "provence-alpes-cote-dazur": ("Provence-Alpes-Côte d’Azur", "🗺️"),
}

# Ces pages ont déjà été mises en forme et validées manuellement.
EXISTING_PAGES = {
    "Baignade-dans-Eygues-Nyons.html": (
        "que-faire-nyons/Baignade-dans-Eygues-Nyons",
        "Baignade dans l’Eygues à Nyons",
        "Précautions utiles avant de se baigner dans la rivière.",
    ),
    "Tour-Randonne.html": (
        "que-faire-nyons/Tour-Randonne-Nyons",
        "Tour Randonne à Nyons",
        "Histoire et visite de l’un des emblèmes de Nyons.",
    ),
    "bike-park-nyons.html": (
        "que-faire-nyons/bike-park-nyons",
        "4Seasons Bike Park Nyons",
        "Pistes VTT, enduro et sensations fortes.",
    ),
    "nyons-avec-des-enfants.html": (
        "que-faire-nyons/nyons-avec-des-enfants",
        "Nyons avec des enfants",
        "Des idées de sorties et d’activités en famille.",
    ),
    "place-buffaven-nyons.html": (
        "que-faire-nyons/place-buffaven-nyons",
        "Place Joseph Buffaven à Nyons",
        "Le marché, la mémoire et la vie de cette place nyonsaise.",
    ),
}

EXTRA_EXISTING = [
    ("que-faire-nyons/Pont-Roman-de-Nyons", "Pont Roman de Nyons", "Le monument emblématique qui enjambe l’Eygues."),
    ("que-faire-nyons/centre-historique-de-nyons", "Centre historique de Nyons", "Ruelles, arcades et patrimoine du vieux Nyons."),
    ("que-faire-nyons/Scourtinerie-de-Nyons", "Scourtinerie de Nyons", "Un savoir-faire local transmis depuis 1882."),
    ("que-faire-nyons/Marche-de-Nyons", "Marché de Nyons", "Le grand marché provençal du jeudi matin."),
]

BLOCK_XPATH = (
    "//body//*[self::h1 or self::h2 or self::h3 or self::p or self::ul "
    "or self::ol or self::iframe]"
    "[not(ancestor::nav)][not(ancestor::footer)][not(ancestor::header)]"
)


def clean_text(node) -> str:
    return " ".join(" ".join(node.itertext()).split())


def slug_for_category_chain(chain: list[str]) -> str:
    if not chain:
        return ""
    return "/".join(CATEGORY_SLUGS.get(item, slugify(item)) for item in chain)


def slugify(value: str) -> str:
    table = str.maketrans(
        "àâäéèêëîïôöùûüÿçœæÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇŒÆ",
        "aaaeeeeiioouuuycoeAA AEEEEIIOOUUUYCOA".replace(" ", ""),
    )
    value = value.translate(table).lower().replace("’", "-").replace("'", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def find_sources(source_root: Path) -> dict[str, Path]:
    sources: dict[str, Path] = {}
    for path in source_root.rglob("*.html"):
        sources.setdefault(path.name, path)
    return sources


def nav_ancestry(anchor) -> list[str]:
    categories: list[str] = []
    node = anchor.getparent()
    while node is not None:
        if node.tag == "li":
            parent_links = node.xpath("./div[1]//a[1]")
            if parent_links and parent_links[0] is not anchor:
                label = clean_text(parent_links[0])
                if label:
                    categories.append(label)
        node = node.getparent()
    return list(reversed(categories))


def build_nav_map(nav_doc) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for anchor in nav_doc.xpath("//nav//a[@href]"):
        href = unquote(anchor.attrib.get("href", ""))
        if href.lower().endswith(".html"):
            result.setdefault(Path(href).name, nav_ancestry(anchor))
    return result


def destination_for(name: str, nav_map: dict[str, list[str]]) -> str:
    if name in EXISTING_PAGES:
        return EXISTING_PAGES[name][0]
    stem = Path(name).stem
    chain = nav_map.get(name, [])
    category_path = slug_for_category_chain(chain)
    category_index_names = {
        "Produits du terroir.html": "produits-du-terroir",
        "questions-utiles-nyons.html": "questions-utiles-nyons",
        "Provence-Alpes-Cote-dAzur.html": "provence-alpes-cote-dazur",
        "Drome.html": "auvergne-rhone-alpes/drome",
    }
    if name in category_index_names:
        return category_index_names[name]
    if category_path:
        return f"{category_path}/{stem}"
    return stem


def resolve_href(href: str, filename: str, destinations: dict[str, str], nav_map: dict[str, list[str]]) -> str:
    if not href:
        return "#"
    if href.startswith("https://www.google.com/url?"):
        href = parse_qs(urlparse(href).query).get("q", [href])[0]
    href = unquote(href)
    target_name = Path(urlparse(href).path).name
    if target_name.lower().endswith(".html"):
        if target_name in destinations:
            return f"{SITE_ROOT}/{destinations[target_name]}/"
        chain = nav_map.get(target_name, [])
        category = slug_for_category_chain(chain)
        stem = Path(target_name).stem
        suffix = f"{category}/{stem}" if category else stem
        return f"{LIVE_ROOT}/{suffix}"
    return href


def inline_html(node, filename: str, destinations: dict[str, str], nav_map: dict[str, list[str]]) -> str:
    chunks: list[str] = []

    def walk(item) -> None:
        if item.text:
            chunks.append(html_std.escape(item.text))
        for child in item:
            tag = child.tag.lower() if isinstance(child.tag, str) else ""
            if tag == "br":
                chunks.append("<br>")
            elif tag in {"strong", "b", "em", "i"}:
                out_tag = "strong" if tag in {"strong", "b"} else "em"
                chunks.append(f"<{out_tag}>")
                walk(child)
                chunks.append(f"</{out_tag}>")
            elif tag == "a":
                href = resolve_href(child.attrib.get("href", ""), filename, destinations, nav_map)
                chunks.append(f'<a href="{html_std.escape(href, quote=True)}">')
                walk(child)
                chunks.append("</a>")
            else:
                walk(child)
            if child.tail:
                chunks.append(html_std.escape(child.tail))

    walk(node)
    return re.sub(r"\s+", " ", "".join(chunks)).strip()


def youtube_id(src: str) -> str | None:
    match = re.search(r"youtube\.com/embed/([A-Za-z0-9_-]{6,})", src)
    if match:
        return match.group(1)
    match = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", src)
    return match.group(1) if match else None


def extract_page(path: Path, destinations: dict[str, str], nav_map: dict[str, list[str]]) -> dict:
    doc = html.parse(str(path))
    blocks = doc.xpath(BLOCK_XPATH)
    h1_positions = [i for i, node in enumerate(blocks) if node.tag.lower() == "h1"]
    if not h1_positions:
        raise ValueError(f"Aucun H1 dans {path.name}")
    first_h1 = h1_positions[0]
    title = clean_text(blocks[first_h1])
    intro = ""
    intro_index: int | None = None
    second_h1 = h1_positions[1] if len(h1_positions) > 1 else first_h1
    for index, node in enumerate(blocks[first_h1 + 1 : second_h1], start=first_h1 + 1):
        if node.tag.lower() == "p" and not node.xpath("ancestor::ul|ancestor::ol"):
            candidate = clean_text(node)
            if candidate and not candidate.startswith("Me suivre"):
                intro = candidate
                intro_index = index
                break
    if not intro:
        for index, node in enumerate(blocks[second_h1 + 1 :], start=second_h1 + 1):
            if node.tag.lower() == "p" and not node.xpath("ancestor::ul|ancestor::ol"):
                intro = clean_text(node)
                if intro:
                    intro_index = index
                    break
    rendered: list[str] = []
    seen_videos: set[str] = set()
    # Certaines vidéos Google Sites sont placées entre le titre de page et le
    # titre de l'article. On repart donc juste après le premier H1.
    start = first_h1 + 1
    for index, node in enumerate(blocks[start:], start=start):
        tag = node.tag.lower()
        if node.xpath("ancestor::ul|ancestor::ol"):
            continue
        if tag == "iframe":
            video = youtube_id(node.attrib.get("src", ""))
            if video and video not in seen_videos:
                seen_videos.add(video)
                rendered.append(
                    '<div class="video"><iframe '
                    f'src="https://www.youtube-nocookie.com/embed/{video}" '
                    f'title="Vidéo : {html_std.escape(title, quote=True)}" '
                    'loading="lazy" allowfullscreen></iframe></div>'
                )
            continue
        text = clean_text(node)
        if not text or text.startswith("🔥 STOP AUX MAUVAISES LOCATIONS") or text.startswith("Me suivre sur"):
            continue
        if index == intro_index:
            continue
        if tag == "h1":
            if index == second_h1 and text == title:
                continue
            rendered.append(f"<h2>{inline_html(node, path.name, destinations, nav_map)}</h2>")
        elif tag in {"h2", "h3"}:
            rendered.append(f"<{tag}>{inline_html(node, path.name, destinations, nav_map)}</{tag}>")
        elif tag == "p":
            rendered.append(f"<p>{inline_html(node, path.name, destinations, nav_map)}</p>")
        elif tag in {"ul", "ol"}:
            items = []
            for li in node.xpath("./li"):
                content = inline_html(li, path.name, destinations, nav_map)
                if content:
                    items.append(f"<li>{content}</li>")
            if items:
                rendered.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
    return {"title": title, "intro": intro, "content": "\n      ".join(rendered), "videos": len(seen_videos)}


def description(text: str, title: str) -> str:
    clean = re.sub(r"\s+", " ", text).strip() or title
    if len(clean) <= 158:
        return clean
    shortened = clean[:158].rsplit(" ", 1)[0].rstrip(" ,;:")
    return shortened + "…"


def nav_html() -> str:
    return (
        f'<header><nav class="nav"><a class="brand" href="{SITE_ROOT}/">🌿 Vivre à Nyons ?</a>'
        '<div class="navlinks">'
        f'<a href="{SITE_ROOT}/que-faire-nyons/">Que faire</a>'
        f'<a href="{SITE_ROOT}/a-faire-autour-de-Nyons/">Autour</a>'
        f'<a href="{SITE_ROOT}/restaurants-de-nyons/">Restaurants</a>'
        f'<a href="{SITE_ROOT}/toutes-les-pages/">Toutes les pages</a>'
        '<a href="https://agenda.vivreanyons.fr/">Agenda</a>'
        '</div></nav></header>'
    )


def agenda_html() -> str:
    return (
        '<section class="agenda"><div class="agenda-head"><div><div class="kicker">Après la lecture</div>'
        '<h2>📅 Que se passe-t-il à Nyons ?</h2></div>'
        '<a href="https://agenda.vivreanyons.fr/">Agenda complet →</a></div>'
        '<div class="agenda-grid" data-agenda><p>Chargement…</p></div></section>'
    )


def page_document(page: dict, destination: str, category: str) -> str:
    label, emoji = CATEGORY_LABELS.get(category.split("/")[0], ("Vivre à Nyons", "🌿"))
    canonical_destination = page.get("canonical_destination", destination)
    canonical = f"{LIVE_ROOT}/{canonical_destination}"
    meta = description(page["intro"], page["title"])
    intro = html_std.escape(page["intro"])
    return f'''<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{html_std.escape(page["title"])} — pilote</title>
  <meta name="description" content="{html_std.escape(meta, quote=True)}">
  <link rel="canonical" href="{html_std.escape(canonical, quote=True)}">
  <link rel="stylesheet" href="{SITE_ROOT}/assets/style.css">
</head>
<body>
  <div class="testbar">🧪 PILOTE — le texte et les vidéos d’abord, une photo sera ajoutée lors de la passe finale</div>
  {nav_html()}
  <section class="hero"><div class="inner"><span class="badge">{emoji} {html_std.escape(label)}</span><h1>{html_std.escape(page["title"])}</h1><p>{intro}</p></div></section>
  <main><div class="wrap content"><article>
      {page["content"]}
    </article>
    {agenda_html()}
  </div></main>
  <footer class="footer"><div class="wrap"><strong>Vivre à Nyons ?</strong><span>contact@vivreanyons.fr · © 2025 VivreAnyons.fr</span><a href="{canonical}">Comparer avec la page actuelle</a></div></footer>
  <script src="{SITE_ROOT}/assets/agenda.js"></script>
</body>
</html>
'''


def index_document(title: str, intro: str, cards: list[tuple[str, str, str]], badge: str) -> str:
    card_html = []
    for destination, card_title, card_intro in sorted(cards, key=lambda item: item[1].casefold()):
        card_html.append(
            '<article class="card"><div class="kicker">Découvrir</div>'
            f'<h2>{html_std.escape(card_title)}</h2><p>{html_std.escape(card_intro)}</p>'
            f'<a href="{SITE_ROOT}/{destination}/">Lire la fiche →</a></article>'
        )
    meta = description(intro, title)
    return f'''<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{html_std.escape(title)} — pilote</title>
<meta name="description" content="{html_std.escape(meta, quote=True)}">
<link rel="stylesheet" href="{SITE_ROOT}/assets/style.css"></head><body>
<div class="testbar">🧪 VERSION PILOTE GITHUB — le site actuel vivreanyons.fr n’est pas modifié</div>
{nav_html()}
<section class="hero"><div class="inner"><span class="badge">{badge}</span><h1>{html_std.escape(title)}</h1><p>{html_std.escape(intro)}</p></div></section>
<main><div class="wrap"><section class="grid">{''.join(card_html)}</section>{agenda_html()}</div></main>
<footer class="footer"><div class="wrap"><strong>Vivre à Nyons ?</strong><span>Version pilote · photos ajoutées lors de la passe finale</span></div></footer>
<script src="{SITE_ROOT}/assets/agenda.js"></script></body></html>
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()

    sources = find_sources(args.sources)
    nav_source = sources.get("decouvrir-nyons.html") or next(iter(sources.values()))
    nav_map = build_nav_map(html.parse(str(nav_source)))
    destinations = {name: destination_for(name, nav_map) for name in sources}
    site_dir = args.repo / "vivreanyons-test"

    pages: list[dict] = []
    failures: list[str] = []
    for name, path in sorted(sources.items()):
        if name in EXISTING_PAGES:
            destination, title, intro = EXISTING_PAGES[name]
            pages.append({"name": name, "destination": destination, "title": title, "intro": intro, "existing": True, "videos": 0})
            continue
        try:
            page = extract_page(path, destinations, nav_map)
        except Exception as exc:
            failures.append(f"{name}: {exc}")
            continue
        destination = destinations[name]
        category = destination.rsplit("/", 1)[0] if "/" in destination else destination
        target = site_dir / destination / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_document(page, destination, category), encoding="utf-8")
        pages.append({"name": name, "destination": destination, **page, "existing": False})

    for destination, title, intro in EXTRA_EXISTING:
        pages.append({"name": "", "destination": destination, "title": title, "intro": intro, "existing": True, "videos": 0})

    category_cards: dict[str, list[tuple[str, str, str]]] = {}
    category_indexes = {"produits-du-terroir", "questions-utiles-nyons", "provence-alpes-cote-dazur", "auvergne-rhone-alpes/drome"}
    for page in pages:
        destination = page["destination"]
        if destination in category_indexes:
            continue
        category = destination.rsplit("/", 1)[0] if "/" in destination else "autres"
        category_cards.setdefault(category, []).append((destination, page["title"], description(page["intro"], page["title"])))

    for category, cards in category_cards.items():
        root_category = category.split("/")[0]
        label, emoji = CATEGORY_LABELS.get(
            category,
            CATEGORY_LABELS.get(root_category, (root_category.replace("-", " ").title(), "🌿")),
        )
        target = site_dir / category / "index.html"
        # L'index Que faire est régénéré avec les fiches validées et importées.
        # Pour les autres rubriques, un index clair remplace l'ancien sommaire Google Sites.
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            index_document(label, f"Retrouve ici toutes les fiches de la rubrique {label.lower()}.", cards, f"{emoji} {label}"),
            encoding="utf-8",
        )

    all_cards = [(p["destination"], p["title"], description(p["intro"], p["title"])) for p in pages]
    all_target = site_dir / "toutes-les-pages" / "index.html"
    all_target.parent.mkdir(parents=True, exist_ok=True)
    all_target.write_text(
        index_document("Toutes les pages de Vivre à Nyons", "Toutes les fiches du site pilote, classées par titre pour retrouver facilement une adresse, un lieu ou un souvenir.", all_cards, "📚 Index complet"),
        encoding="utf-8",
    )

    home_cards: list[tuple[str, str, str]] = []
    for category, cards in category_cards.items():
        root_category = category.split("/")[0]
        label, emoji = CATEGORY_LABELS.get(
            category,
            CATEGORY_LABELS.get(root_category, (root_category.replace("-", " ").title(), "🌿")),
        )
        home_cards.append((category, f"{emoji} {label}", f"{len(cards)} fiche{'s' if len(cards) > 1 else ''} dans cette rubrique."))
    home_cards.append(("toutes-les-pages", "📚 Toutes les pages", f"{len(pages)} fiches classées par titre."))
    (site_dir / "index.html").write_text(
        index_document(
            "Vivre à Nyons, simplement.",
            "Découvrir Nyons, ses bonnes adresses, son patrimoine, son terroir et les villages alentour grâce à des fiches faciles à retrouver.",
            home_cards,
            "☀️ Nyons · Drôme Provençale",
        ),
        encoding="utf-8",
    )

    # Les anciennes fiches validées gardent leur contenu, mais reçoivent la
    # même navigation que toutes les nouvelles pages.
    header_pattern = re.compile(r"<header><nav\b.*?</nav></header>", re.S)
    for target in site_dir.rglob("index.html"):
        source = target.read_text(encoding="utf-8")
        updated = header_pattern.sub(nav_html(), source, count=1)
        if updated != source:
            target.write_text(updated, encoding="utf-8")

    print(f"Sources uniques : {len(sources)}")
    print(f"Pages générées : {sum(not p['existing'] for p in pages)}")
    print(f"Pages conservées : {sum(bool(p['existing']) for p in pages)}")
    print(f"Vidéos conservées : {sum(int(p.get('videos', 0)) for p in pages)}")
    print(f"Rubriques : {len(category_cards)}")
    if failures:
        print("ÉCHECS")
        print("\n".join(failures))


if __name__ == "__main__":
    main()

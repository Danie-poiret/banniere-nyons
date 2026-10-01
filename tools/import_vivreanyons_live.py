#!/usr/bin/env python3
"""Complète le pilote avec toutes les pages visibles sur vivreanyons.fr.

Le menu Google Sites contient la liste complète des pages. Ce script la lit,
télécharge les pages en parallèle, conserve le texte et les vidéos YouTube,
puis génère des index de rubriques propres. Le site public n'est jamais modifié.
"""

from __future__ import annotations

import argparse
import html as html_std
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from lxml import html

from import_vivreanyons_drive import (
    CATEGORY_LABELS,
    EXTRA_EXISTING,
    LIVE_ROOT,
    SITE_ROOT,
    agenda_html,
    clean_text,
    description,
    index_document,
    nav_html,
    page_document,
    youtube_id,
)


HOME_URL = f"{LIVE_ROOT}/accueil"
USER_AGENT = "Mozilla/5.0 (compatible; VivreAnyonsMigration/1.0)"
BLOCK_XPATH = (
    "//body//*[self::h1 or self::h2 or self::h3 or self::p or self::ul "
    "or self::ol or self::iframe]"
    "[not(ancestor::nav)][not(ancestor::footer)][not(ancestor::header)]"
)

# Ces fiches ont déjà été corrigées et validées manuellement dans le pilote.
PRESERVED_DESTINATIONS = {
    "que-faire-nyons/Baignade-dans-Eygues-Nyons",
    "que-faire-nyons/Tour-Randonne-Nyons",
    "que-faire-nyons/bike-park-nyons",
    "que-faire-nyons/nyons-avec-des-enfants",
    "que-faire-nyons/place-buffaven-nyons",
    "que-faire-nyons/Pont-Roman-de-Nyons",
    "que-faire-nyons/centre-historique-de-nyons",
    "que-faire-nyons/Scourtinerie-de-Nyons",
    "que-faire-nyons/Marche-de-Nyons",
}

# Quelques anciennes URL aboutissent à une fiche validée dont le chemin pilote
# est déjà différent. On évite ainsi de recréer un doublon.
SOURCE_TO_PRESERVED = {
    "infos-pratiques-nyons/Baignade-dans-Eygues-Nyons": "que-faire-nyons/Baignade-dans-Eygues-Nyons",
    "que-faire-nyons/Tour-Randonne": "que-faire-nyons/Tour-Randonne-Nyons",
    "video-nyons/place-buffaven-nyons": "que-faire-nyons/place-buffaven-nyons",
}

BOILERPLATE_PREFIXES = (
    "🔥 STOP AUX MAUVAISES LOCATIONS",
    "Me suivre sur",
    "Page updated",
    "Report abuse",
    "This site uses cookies",
)

# Premières rubriques créées depuis l'export Drive avec des URL simplifiées.
# L'import du site public conserve désormais les vraies URL pour éviter les
# doublons et préparer une migration sans perte de référencement.
STALE_GENERATED_DIRS = (
    "que-faire-autour-de-nyons",
    "histoire-de-nyons-en-video",
    "histoire-geo",
    "auvergne-rhone-alpes",
    "provence-alpes-cote-dazur",
)


def fetch(url: str, retries: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=45) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - réseau variable
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Téléchargement impossible : {url}: {last_error}")


def discover_urls() -> list[str]:
    doc = html.fromstring(fetch(HOME_URL), base_url=HOME_URL)
    urls: set[str] = set()
    for href in doc.xpath("//a[@href]/@href"):
        absolute = urldefrag(urljoin(HOME_URL, href))[0]
        parsed = urlparse(absolute)
        if parsed.scheme in {"http", "https"} and parsed.netloc == "www.vivreanyons.fr":
            path = parsed.path.rstrip("/") or "/accueil"
            urls.add(f"{LIVE_ROOT}{path}")
    return sorted(urls, key=lambda value: urlparse(value).path.casefold())


def source_path(url: str) -> str:
    return urlparse(url).path.strip("/") or "accueil"


def destination_for(source: str) -> str:
    return SOURCE_TO_PRESERVED.get(source, source)


def inline_html(node, url_map: dict[str, str]) -> str:
    chunks: list[str] = []

    def resolve(href: str) -> str:
        absolute = urldefrag(urljoin(HOME_URL, href))[0]
        parsed = urlparse(absolute)
        if parsed.netloc == "www.vivreanyons.fr":
            source = parsed.path.strip("/") or "accueil"
            destination = url_map.get(source)
            if destination == "":
                return f"{SITE_ROOT}/"
            if destination:
                return f"{SITE_ROOT}/{destination}/"
        return href

    def walk(item) -> None:
        if item.text:
            chunks.append(html_std.escape(item.text))
        for child in item:
            tag = child.tag.lower() if isinstance(child.tag, str) else ""
            if tag == "br":
                chunks.append("<br>")
            elif tag in {"strong", "b", "em", "i"}:
                output_tag = "strong" if tag in {"strong", "b"} else "em"
                chunks.append(f"<{output_tag}>")
                walk(child)
                chunks.append(f"</{output_tag}>")
            elif tag == "a":
                href = resolve(child.attrib.get("href", ""))
                chunks.append(f'<a href="{html_std.escape(href, quote=True)}">')
                walk(child)
                chunks.append("</a>")
            else:
                walk(child)
            if child.tail:
                chunks.append(html_std.escape(child.tail))

    walk(node)
    return re.sub(r"\s+", " ", "".join(chunks)).strip()


def extract_page(raw: bytes, source: str, url_map: dict[str, str]) -> dict:
    doc = html.fromstring(raw)
    blocks = doc.xpath(BLOCK_XPATH)
    h1_positions = [index for index, node in enumerate(blocks) if node.tag.lower() == "h1"]
    if not h1_positions:
        raise ValueError("aucun H1")

    first_h1 = h1_positions[0]
    second_h1 = h1_positions[1] if len(h1_positions) > 1 else first_h1
    title = clean_text(blocks[first_h1])
    if len(h1_positions) > 1:
        article_title = clean_text(blocks[second_h1])
        if article_title and len(article_title) > len(title) / 2:
            title = article_title

    intro = ""
    intro_index: int | None = None
    search_ranges = [
        range(first_h1 + 1, second_h1),
        range(second_h1 + 1, len(blocks)),
    ]
    for indexes in search_ranges:
        for index in indexes:
            node = blocks[index]
            if node.tag.lower() != "p" or node.xpath("ancestor::ul|ancestor::ol"):
                continue
            candidate = clean_text(node)
            if candidate and not candidate.startswith(BOILERPLATE_PREFIXES):
                intro = candidate
                intro_index = index
                break
        if intro:
            break

    rendered: list[str] = []
    seen_videos: set[str] = set()
    for index, node in enumerate(blocks[first_h1 + 1 :], start=first_h1 + 1):
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
        if not text or text.startswith(BOILERPLATE_PREFIXES) or index == intro_index:
            continue
        if tag == "h1":
            if index == second_h1 and text == title:
                continue
            rendered.append(f"<h2>{inline_html(node, url_map)}</h2>")
        elif tag in {"h2", "h3"}:
            rendered.append(f"<{tag}>{inline_html(node, url_map)}</{tag}>")
        elif tag == "p":
            rendered.append(f"<p>{inline_html(node, url_map)}</p>")
        elif tag in {"ul", "ol"}:
            items = []
            for li in node.xpath("./li"):
                content = inline_html(li, url_map)
                if content:
                    items.append(f"<li>{content}</li>")
            if items:
                rendered.append(f"<{tag}>" + "".join(items) + f"</{tag}>")

    if not intro:
        intro = title
    return {
        "title": title,
        "intro": intro,
        "content": "\n      ".join(rendered),
        "videos": len(seen_videos),
        "canonical_destination": source,
    }


def read_existing_page(target: Path, destination: str) -> dict:
    doc = html.parse(str(target))
    title = clean_text(doc.xpath("//h1")[0]) if doc.xpath("//h1") else destination.rsplit("/", 1)[-1]
    intro_nodes = doc.xpath("//section[contains(@class,'hero')]//p[1]")
    intro = clean_text(intro_nodes[0]) if intro_nodes else title
    return {"title": title, "intro": intro, "destination": destination, "existing": True, "videos": 0}


def label_for(category: str) -> tuple[str, str]:
    if category in CATEGORY_LABELS:
        return CATEGORY_LABELS[category]
    aliases = {
        "a-faire-autour-de-Nyons": ("À découvrir autour de Nyons", "🚗"),
        "video-nyons": ("Nyons en vidéo", "🎬"),
        "Histoire-Geo": ("Histoire et mémoire", "🏛️"),
        "randonnee-nyons": ("Randonnées autour de Nyons", "🥾"),
        "nyons-carte-interactive": ("Cartes interactives de Nyons", "🗺️"),
        "Auvergne-Rhone-Alpes": ("Auvergne-Rhône-Alpes", "🗺️"),
        "Auvergne-Rhone-Alpes/Drome": ("Drôme", "🏞️"),
        "Auvergne-Rhone-Alpes/Rhone": ("Rhône et Lyon", "🏙️"),
        "Provence-Alpes-Cote-dAzur": ("Provence-Alpes-Côte d’Azur", "🗺️"),
        "Provence-Alpes-Cote-dAzur/Vaucluse": ("Vaucluse", "☀️"),
    }
    if category in aliases:
        return aliases[category]
    return category.rsplit("/", 1)[-1].replace("-", " ").title(), "🌿"


def category_for(destination: str) -> str:
    return destination.rsplit("/", 1)[0] if "/" in destination else "autres"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    site_dir = args.repo / "vivreanyons-test"
    for relative in STALE_GENERATED_DIRS:
        stale = site_dir / relative
        if stale.is_dir():
            shutil.rmtree(stale)
    urls = discover_urls()
    sources = [source_path(url) for url in urls]
    url_map = {source: ("" if source == "accueil" else destination_for(source)) for source in sources}

    # Une URL qui est le parent direct d'autres pages devient un index de rubrique.
    source_set = set(sources)
    category_sources = {
        source
        for source in source_set
        if source == "accueil" or any(other.startswith(source + "/") for other in source_set)
    }
    page_urls = [url for url in urls if source_path(url) not in category_sources]

    downloaded: dict[str, bytes] = {}
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(fetch, url): url for url in page_urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                downloaded[source_path(url)] = future.result()
            except Exception as exc:
                failures.append(f"{url}: {exc}")

    pages: list[dict] = []
    for source in sorted(downloaded, key=str.casefold):
        destination = destination_for(source)
        target = site_dir / destination / "index.html"
        if destination in PRESERVED_DESTINATIONS and target.exists():
            pages.append(read_existing_page(target, destination))
            continue
        try:
            page = extract_page(downloaded[source], source, url_map)
        except Exception as exc:
            failures.append(f"{source}: {exc}")
            continue
        category = category_for(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_document(page, destination, category), encoding="utf-8")
        pages.append({"destination": destination, **page, "existing": False})

    # Les pages conservées peuvent ne pas avoir une URL source unique dans le menu.
    known_destinations = {page["destination"] for page in pages}
    for destination, title, intro in EXTRA_EXISTING:
        if destination not in known_destinations:
            pages.append({"destination": destination, "title": title, "intro": intro, "existing": True, "videos": 0})

    category_cards: dict[str, list[tuple[str, str, str]]] = {}
    for page in pages:
        destination = page["destination"]
        category = category_for(destination)
        category_cards.setdefault(category, []).append(
            (destination, page["title"], description(page["intro"], page["title"]))
        )

    # Les régions comme Auvergne-Rhône-Alpes ne contiennent que des
    # sous-rubriques (Drôme, Rhône). Elles doivent tout de même avoir leur page.
    all_categories = sorted(category_sources - {"accueil"}, key=lambda value: (value.count("/"), value.casefold()), reverse=True)
    for category in all_categories:
        direct_children = []
        for child in all_categories:
            if child.rsplit("/", 1)[0] != category or child == category:
                continue
            child_label, child_emoji = label_for(child)
            child_count = len(category_cards.get(child, []))
            direct_children.append(
                (child, f"{child_emoji} {child_label}", f"{child_count} fiche{'s' if child_count > 1 else ''} dans cette rubrique.")
            )
        if direct_children:
            category_cards.setdefault(category, []).extend(direct_children)

    for category, cards in category_cards.items():
        label, emoji = label_for(category)
        target = site_dir / category / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            index_document(label, f"Retrouve ici toutes les fiches de la rubrique {label.lower()}.", cards, f"{emoji} {label}"),
            encoding="utf-8",
        )

    all_cards = [(page["destination"], page["title"], description(page["intro"], page["title"])) for page in pages]
    (site_dir / "toutes-les-pages").mkdir(parents=True, exist_ok=True)
    (site_dir / "toutes-les-pages" / "index.html").write_text(
        index_document(
            "Toutes les pages de Vivre à Nyons",
            "Toutes les fiches du site pilote, classées par titre pour retrouver facilement une adresse, un lieu ou un souvenir.",
            all_cards,
            "📚 Index complet",
        ),
        encoding="utf-8",
    )

    home_cards = []
    for category, cards in category_cards.items():
        if "/" in category:
            continue
        label, emoji = label_for(category)
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

    header_pattern = re.compile(r"<header><nav\b.*?</nav></header>", re.S)
    for target in site_dir.rglob("index.html"):
        current = target.read_text(encoding="utf-8")
        updated = header_pattern.sub(nav_html(), current, count=1)
        if updated != current:
            target.write_text(updated, encoding="utf-8")

    print(f"URL découvertes : {len(urls)}")
    print(f"Rubriques détectées : {len(category_sources) - 1}")
    print(f"Fiches téléchargées : {len(downloaded)}")
    print(f"Fiches publiées dans le pilote : {len(pages)}")
    print(f"Vidéos conservées : {sum(int(page.get('videos', 0)) for page in pages)}")
    print(f"Échecs : {len(failures)}")
    if failures:
        print("\n".join(failures))


if __name__ == "__main__":
    main()

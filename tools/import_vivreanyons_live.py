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

from lxml import etree, html

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
SOURCE_TO_PRESERVED: dict[str, str] = {}

# Deux fiches mises en forme manuellement restent proposées comme raccourcis,
# en plus des URL originales qui sont désormais toutes conservées.
PRESERVED_ALIASES = {
    "que-faire-nyons/Baignade-dans-Eygues-Nyons": "infos-pratiques-nyons/Baignade-dans-Eygues-Nyons",
    "que-faire-nyons/place-buffaven-nyons": "video-nyons/place-buffaven-nyons",
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


def synchronize_original_titles(site_dir: Path, downloaded: dict[str, bytes]) -> int:
    """Recopie le premier H1 de chaque page Google Sites dans le pilote."""
    updated_count = 0
    for source, raw in downloaded.items():
        destination = destination_for(source)
        target = site_dir / destination / "index.html"
        if not target.exists():
            continue
        original = html.fromstring(raw)
        original_h1 = original.xpath("//h1")
        if not original_h1:
            continue
        title = clean_text(original_h1[0])
        if not title:
            continue
        document = html.parse(str(target))
        target_h1 = document.xpath("//h1[1]")
        title_nodes = document.xpath("//title")
        canonical = document.xpath('//link[@rel="canonical"]')
        if not target_h1:
            continue
        target_h1[0].clear()
        target_h1[0].text = title
        if title_nodes:
            title_nodes[0].text = f"{title} — pilote"
        if canonical:
            canonical[0].attrib["href"] = f"{LIVE_ROOT}/{source}"
        target.write_text(
            html.tostring(document, encoding="unicode", method="html", doctype="<!doctype html>"),
            encoding="utf-8",
        )
        updated_count += 1

    # Les deux raccourcis manuels pointent vers la vraie page source.
    for alias, source in PRESERVED_ALIASES.items():
        target = site_dir / alias / "index.html"
        if not target.exists():
            continue
        document = html.parse(str(target))
        canonical = document.xpath('//link[@rel="canonical"]')
        if canonical:
            canonical[0].attrib["href"] = f"{LIVE_ROOT}/{source}"
            target.write_text(
                html.tostring(document, encoding="unicode", method="html", doctype="<!doctype html>"),
                encoding="utf-8",
            )
    return updated_count


def short_topic(title: str) -> str:
    parts = re.split(r"\s*[:–—|]\s*", title)
    generic_prefixes = {"vidéo", "video", "photo", "photos", "image", "images"}
    if len(parts) > 1 and parts[0].strip().casefold() in generic_prefixes:
        topic = parts[1].strip(" ?.! ")
    else:
        topic = parts[0].strip(" ?.! ")
    words = topic.split()
    if len(words) > 12:
        topic = " ".join(words[:12])
    return topic or title


def generated_h2(destination: str, topic: str) -> str:
    category = destination.split("/", 1)[0]
    if category == "restaurants-de-nyons":
        return f"Découvrir {topic}"
    if category == "ou-dormir-a-nyons":
        return f"Séjourner à {topic}"
    if category in {"video-nyons", "Histoire-Geo"}:
        return f"Histoire et mémoire : {topic}"
    if category == "infos-pratiques-nyons":
        return f"Ce qu’il faut savoir sur {topic}"
    if category == "evenements-nyons":
        return f"Tout savoir sur {topic}"
    if category == "questions-utiles-nyons":
        return f"Les réponses utiles sur {topic}"
    if category in {"nyons-image-1", "photos2", "photos-nyons-3", "photos-4"}:
        return "Nyons en images"
    return f"Découvrir {topic}"


def heading_sentences(text: str) -> list[str]:
    """Découpe un paragraphe en phrases utilisables comme intertitres."""
    clean = re.sub(r"\s+", " ", text).strip()
    return [part.strip(" \t\n\r-–—•") for part in re.split(r"(?<=[.!?])\s+", clean) if part.strip()]


def clean_semantic_heading(text: str) -> str:
    """Transforme une phrase du texte en H2 court sans en changer le sens."""
    heading = re.sub(r"\s+", " ", text).strip(" \t\n\r-–—•\"“”«».!?;:")
    heading = re.sub(r"^(?:Et puis|Alors|Déjà|Évidemment|En réalité|D’ailleurs|Bref),?\s+", "", heading, flags=re.I)
    heading = re.sub(
        r"^Ce que (?:j’aime|j’ai aimé|j’adore|j’ai adoré)(?: aussi)?, c’est que\s+",
        "",
        heading,
        flags=re.I,
    )
    heading = re.sub(
        r"^Ce qui ressort de (?:tous )?les clients(?: et que .*?)? c’est\s+",
        "",
        heading,
        flags=re.I,
    )
    heading = re.sub(r"^Pour résumer(?: simplement)?,?\s+", "", heading, flags=re.I)
    heading = re.sub(r"^En résumé\s*:\s*", "", heading, flags=re.I)
    heading = re.sub(r"^(?:Oui|Non),\s+", "", heading, flags=re.I)
    heading = re.sub(
        r"^Ça diversifie l’offre locale, ça surprend, ça ouvre des portes$",
        "Une adresse qui diversifie l’offre locale et ouvre de nouvelles portes",
        heading,
        flags=re.I,
    )

    # Un intertitre doit rester lisible : on conserve une proposition complète
    # plutôt qu'une longue phrase d'article.
    if len(heading) > 118:
        clauses = re.split(r"\s+[–—:]\s+|;\s+", heading)
        useful = next((part for part in clauses if 38 <= len(part) <= 118), "")
        if useful:
            heading = useful.strip()
        else:
            return ""
    if heading:
        if heading[0].isdigit():
            heading = f"Les {heading}"
        heading = heading[0].upper() + heading[1:]
    return heading.rstrip(" .!?;:")


def thematic_heading(text: str, category: str) -> tuple[str, str] | None:
    """Rédige un intertitre à partir de thèmes explicitement présents dans le passage."""
    clean = re.sub(r"\s+", " ", text).strip()
    lower = clean.casefold()

    def has(pattern: str) -> bool:
        return bool(re.search(pattern, lower, re.I))

    if has(r"\b(?:adresse|horaires?|téléphone|email|accès)\b"):
        return "Adresse, accès et informations pratiques", "pratique"
    if category == "infos-pratiques-nyons" and has(r"\b(?:parking|stationnement|navette|places? gratuites?)\b"):
        if has(r"navette"):
            return "La navette complète les solutions de stationnement", "stationnement"
        return "Les solutions de stationnement à connaître", "stationnement"
    if category == "restaurants-de-nyons" and has(r"\b(?:saumon|sashimis?|makis?|sushis?)\b"):
        foods = []
        for pattern, label in (
            (r"\bsaumon\b", "Saumon"),
            (r"\bsashimis?\b", "sashimis"),
            (r"\bmakis?\b", "makis"),
            (r"\bsushis?\b", "sushis"),
            (r"\bthon\b", "thon"),
        ):
            if re.search(pattern, lower, re.I) and label.casefold() not in {item.casefold() for item in foods}:
                foods.append(label)
        subject = foods[0] if len(foods) == 1 else " et ".join(foods) if len(foods) == 2 else ", ".join(foods[:2]) + f" et {foods[2]}"
        if has(r"\b(?:frais|fraîcheur|frais du jour)\b"):
            return f"{subject} mettent la fraîcheur au premier plan", "cuisine-japonaise"
        return f"{subject} composent une assiette aux saveurs japonaises", "cuisine-japonaise"
    if category == "restaurants-de-nyons" and has(r"\b(?:brochettes?|burgers?|bagels?|sauces? maison)\b"):
        foods = []
        for pattern, label in (
            (r"\bbrochettes?\b", "Brochettes"),
            (r"\bburgers?\b", "burgers"),
            (r"\bbagels?\b", "bagels"),
            (r"\bsauces? maison\b", "sauces maison"),
        ):
            if re.search(pattern, lower, re.I):
                foods.append(label)
        subject = foods[0] if len(foods) == 1 else " et ".join(foods) if len(foods) == 2 else ", ".join(foods[:2]) + f" et {foods[2]}"
        return f"{subject} donnent son caractère à la carte", "specialites"
    if category == "restaurants-de-nyons" and has(r"\b(?:risotto|desserts?|gâteaux?|cake|plats? du jour|cuisine végétale|vegan)\b"):
        if has(r"\b(?:végétal|vegan)\w*\b"):
            return "La cuisine végétale se veut gourmande et généreuse", "cuisine-vegetale"
        return "Les plats et desserts complètent une carte gourmande", "plats-desserts"
    if category in {"restaurants-de-nyons", "ou-dormir-a-nyons", "que-faire-nyons"} and has(r"\b(?:accueil|gentillesse|sourire|souriant|chaleureux|convivial)\w*\b"):
        return "L’accueil chaleureux fait pleinement partie de l’expérience", "accueil"
    if has(r"\b(?:frais|fraîcheur|fait maison|faits maison|préparé sur place)\b"):
        return "La fraîcheur et le fait maison reviennent dans les témoignages", "fraicheur"
    if has(r"\b(?:fabrication|fabriqué|atelier|savoir-faire)\b"):
        if has(r"\b(?:voir|aperçu|depuis la boutique|visite)\b"):
            return "La fabrication se laisse entrevoir pendant la visite", "fabrication"
        return "La fabrication met en valeur un savoir-faire local", "fabrication"
    if has(r"\b(?:savons?|parfums?|shampoings? solides?|peau douce)\b"):
        if has(r"\b(?:choix|dizaines|gammes?)\b"):
            return "Savons et parfums offrent un choix particulièrement large", "savons"
        return "Les savons sont appréciés pour leurs parfums et leur douceur", "savons"
    if has(r"\b(?:composition|ingrédients?|huile de palme|origine)\b"):
        return "La composition des produits suscite aussi des questions", "composition"
    if has(r"\b(?:commande|livraison|colis|boutique en ligne)\b"):
        return "La commande en ligne reçoit elle aussi des avis positifs", "commande"
    if has(r"\b(?:prix|tarifs?|rapport qualité.prix|cher|abordable)\b"):
        if has(r"\b(?:partagés?|contrastés?|certains|d’autres)\b"):
            return "Les prix donnent lieu à des avis plus partagés", "prix"
        return "Les tarifs et le rapport qualité-prix en pratique", "prix"
    if has(r"ni parfait,? ni catastrophique|lieu plaisir"):
        return "Une visite plaisir malgré quelques avis plus nuancés", "bilan"
    if category in {"restaurants-de-nyons", "ou-dormir-a-nyons", "que-faire-nyons", "a-faire-autour-de-Nyons", "randonnee-nyons"} and has(r"\b(?:enfants?|familles?|aire de jeux|toboggan)\b"):
        if has(r"\bcapfun\b|\bparc aquatique\b"):
            return "Le parc aquatique prolonge la sortie en famille", "famille"
        return "Une découverte qui peut aussi se partager en famille", "famille"
    if has(r"\b(?:remparts?|prieuré|chapelle|église|château|mosaïque|bas-relief|patrimoine)\b"):
        details = []
        for pattern, label in (
            (r"\bremparts?\b", "Remparts"),
            (r"\bprieuré\b", "prieuré"),
            (r"\bchapelle\b", "chapelle"),
            (r"\béglise\b", "église"),
            (r"\bchâteau\b", "château"),
            (r"\bmosaïque\b", "mosaïque"),
        ):
            if re.search(pattern, lower, re.I):
                details.append(label)
        if len(details) >= 2:
            subject = details[0] if len(details) == 1 else " et ".join(details) if len(details) == 2 else ", ".join(details[:2]) + f" et {details[2]}"
            return f"{subject} racontent le patrimoine local", "patrimoine"
        return "Le patrimoine local raconte plusieurs siècles d’histoire", "patrimoine"
    if has(r"\b(?:xii|xiii|xiv|xv|xvi|xvii|xviii|xix|xx)e? siècle\b|\bautrefois\b|\bhistoire\b"):
        return "Une histoire locale qui reste visible aujourd’hui", "histoire"
    if has(r"\b(?:vignes?|vins?|rouges?|rosés?|blancs?|cave|terroir)\b"):
        if has(r"\b(?:rouges?|rosés?|blancs?)\b"):
            return "Rouges, rosés et blancs expriment le terroir local", "vins"
        return "Vignes et vins façonnent le caractère du lieu", "vins"
    if category != "restaurants-de-nyons" and (has(r"\b(?:randonnée|rando|sentier)\b") or (
        category in {"randonnee-nyons", "a-faire-autour-de-Nyons"}
        and has(r"\b(?:balade|marcher|promenade)\b")
    )):
        if has(r"\b(?:gourmande|dégustation|terroirs?)\b"):
            return "La randonnée gourmande mêle marche et dégustations", "randonnee"
        return "Le sentier révèle le paysage au fil de la marche", "randonnee"
    if has(r"\b(?:panorama|point de vue|vue sur|paysage|horizon)\b"):
        return "Le panorama devient l’un des temps forts de la découverte", "panorama"
    if has(r"\b(?:piscine|bassin|baignade|parc aquatique)\b"):
        return "La baignade apporte une pause bienvenue pendant la visite", "baignade"
    if has(r"\b(?:chambres? d.hôtes|gîtes?|hébergement|hôtel|camping)\b"):
        return "Plusieurs solutions permettent de prolonger le séjour", "hebergement"
    if has(r"\b(?:marché|commerces?|boutiques?|centre-ville)\b"):
        return "Le centre et ses commerces se découvrent à pied", "centre"
    if category not in {"video-nyons", "Histoire-Geo"} and has(r"\b(?:avis|commentaires?|témoignages?|clients?|visiteurs?|vacanciers?)\b"):
        return "Les témoignages font ressortir les mêmes points forts", "temoignages"
    return None


def semantic_heading(
    paragraphs: list[str], used: set[str], used_themes: set[str], category: str
) -> tuple[str, str, int]:
    """Choisit une affirmation réelle du passage, dans le style d'un bon titre éditorial."""
    candidates: list[tuple[int, str, str, int]] = []
    first_person = re.compile(r"\b(?:je|j’|j'|moi|mon|ma|mes|nous|notre|nos)\b", re.I)
    second_person = re.compile(r"\b(?:tu|vous|votre|vos)\b", re.I)
    weak_start = re.compile(r"^(?:il|elle|ils|elles|cela|ça|c’|c'|on)\b", re.I)
    dependent_start = re.compile(
        r"^(?:à l’accueil|alors|côté|d’autres|et |ici|le genre|pour beaucoup|tout ce|voilà|en sortant|après ça)",
        re.I,
    )
    useful_words = re.compile(
        r"\b(?:accueil|ambiance|adresse|atelier|boutique|château|choix|cuisine|église|"
        r"fabrication|fraîcheur|histoire|maison|marché|menu|panorama|parking|patrimoine|"
        r"paysage|produit|restaurant|saveur|sentier|service|spécialité|village|vue)\w*\b",
        re.I,
    )

    def too_similar(heading: str) -> bool:
        stop = {
            "dans", "avec", "pour", "chez", "cette", "entre", "aussi", "plus", "moins",
            "fait", "font", "partie", "comme", "tout", "tous", "toute", "toutes", "une",
            "des", "les", "aux", "sur", "son", "ses", "leur", "leurs", "qui", "que",
        }
        tokens = {word for word in re.findall(r"[a-zà-ÿ]{4,}", heading.casefold()) if word not in stop}
        for previous in used:
            other = {word for word in re.findall(r"[a-zà-ÿ]{4,}", previous) if word not in stop}
            if tokens and other and len(tokens & other) / min(len(tokens), len(other)) >= 0.6:
                return True
        return False

    for paragraph_rank, paragraph in enumerate(paragraphs):
        thematic = thematic_heading(paragraph, category)
        if thematic:
            thematic_text = clean_semantic_heading(thematic[0])
            if (
                thematic_text
                and thematic[1] not in used_themes
                and thematic_text.casefold() not in used
                and not too_similar(thematic_text)
            ):
                candidates.append((64 - paragraph_rank * 4, thematic_text, thematic[1], paragraph_rank))
        for sentence_rank, sentence in enumerate(heading_sentences(paragraph)):
            heading = clean_semantic_heading(sentence)
            length = len(heading)
            if not 28 <= length <= 118:
                continue
            if re.search(r"https?://|www\.|@|\b\d{2}[ .]\d{2}[ .]\d{2}", heading, re.I):
                continue
            if re.match(r"^(?:adresse|horaires?|téléphone|email)\b", heading, re.I):
                continue
            if heading.casefold() in used or too_similar(heading):
                continue
            score = 40 - paragraph_rank * 3 - sentence_rank
            if 45 <= length <= 96:
                score += 10
            if useful_words.search(heading):
                score += 8
            if first_person.search(heading):
                score -= 8
            if second_person.search(heading):
                score -= 10
            if weak_start.search(heading):
                score -= 5
            if dependent_start.search(heading):
                score -= 14
            if re.search(r"\b(?:est|sont|reste|revient|devient|offre|propose|permet|fait|donne|apporte|séduit)\b", heading, re.I):
                score += 5
            sentence_theme = thematic_heading(heading, category)
            theme_key = sentence_theme[1] if sentence_theme else ""
            if theme_key and theme_key in used_themes:
                continue
            candidates.append((score, heading, theme_key, paragraph_rank))

    if candidates:
        candidates.sort(key=lambda item: (-item[0], len(item[1])))
        return candidates[0][1], candidates[0][2], candidates[0][3]

    # Dernier recours : les premiers mots du passage restent strictement
    # extractifs, donc aucune information n'est inventée.
    fallback = clean_semantic_heading(paragraphs[0]) if paragraphs else "Un autre aspect à découvrir"
    return fallback or "Un autre aspect à découvrir", "", 0


def add_semantic_h2s(article: etree._Element, destination: str) -> int:
    """Découpe les longues fiches pauvres en H2 avec des titres tirés de leur texte."""
    for old in article.xpath('.//h2[contains(concat(" ", normalize-space(@class), " "), " generated-semantic-h2 ")]'):
        parent = old.getparent()
        if parent is not None:
            parent.remove(old)

    # Certains anciens articles contenaient deux fois le même intertitre.
    # Une seule occurrence suffit et évite une structure éditoriale artificielle.
    seen_headings: set[str] = set()
    for heading in list(article.xpath("./h2")):
        label = clean_text(heading).casefold()
        if label in seen_headings:
            parent = heading.getparent()
            if parent is not None:
                parent.remove(heading)
        else:
            seen_headings.add(label)

    paragraphs = [node for node in article.xpath("./p") if len(clean_text(node)) >= 55]
    current_h2s = article.xpath("./h2")
    paragraph_count = len(paragraphs)
    if paragraph_count < 3 or len(current_h2s) >= 3:
        return 0

    desired_total = 2 if paragraph_count <= 7 else 3 if paragraph_count <= 11 else 4 if paragraph_count <= 18 else 5 if paragraph_count <= 28 else 6
    missing = max(0, desired_total - len(current_h2s))
    if not missing:
        return 0

    # Les positions sont réparties dans l'article, jamais avant l'introduction.
    positions: list[int] = []
    for number in range(1, missing + 1):
        index = round(paragraph_count * number / (missing + 1))
        index = max(2, min(paragraph_count - 1, index))
        while index in positions and index < paragraph_count - 1:
            index += 1
        positions.append(index)

    used = {clean_text(node).casefold() for node in current_h2s}
    used_themes: set[str] = set()
    category = destination.split("/", 1)[0]
    inserted = 0
    for index in positions:
        nearby = [clean_text(candidate) for candidate in paragraphs[index : min(paragraph_count, index + 3)]]
        heading_text, theme_key, paragraph_offset = semantic_heading(nearby, used, used_themes, category)
        node = paragraphs[min(paragraph_count - 1, index + paragraph_offset)]
        if heading_text.casefold() in used:
            continue
        heading = html.Element("h2", {"class": "generated-semantic-h2"})
        heading.text = heading_text
        node.addprevious(heading)
        used.add(heading_text.casefold())
        if theme_key:
            used_themes.add(theme_key)
        inserted += 1
    return inserted


def compact_answer(text: str, limit: int = 430) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    kept: list[str] = []
    for sentence in sentences:
        candidate = " ".join(kept + [sentence])
        if len(candidate) > limit and kept:
            break
        kept.append(sentence)
        if len(candidate) >= limit * 0.65:
            break
    answer = " ".join(kept).strip()
    if not answer:
        answer = clean[:limit].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return answer


def faq_questions(destination: str, topic: str, has_practical: bool) -> list[str]:
    category = destination.split("/", 1)[0]
    middle = {
        "restaurants-de-nyons": f"Que peut-on découvrir chez « {topic} » ?",
        "ou-dormir-a-nyons": f"Pourquoi choisir « {topic} » pour un séjour ?",
        "video-nyons": f"Quelle histoire locale est liée à « {topic} » ?",
        "Histoire-Geo": f"Quelle histoire locale est liée à « {topic} » ?",
        "infos-pratiques-nyons": f"Quel détail pratique faut-il retenir sur « {topic} » ?",
        "evenements-nyons": f"Comment profiter de « {topic} » ?",
        "produits-du-terroir": f"Qu’est-ce qui caractérise « {topic} » ?",
        "randonnee-nyons": f"Que découvre-t-on pendant « {topic} » ?",
    }.get(category, f"Pourquoi découvrir « {topic} » ?")
    last = (
        f"Quelle information pratique retenir sur « {topic} » ?"
        if has_practical
        else f"Quel autre détail ressort de l’article sur « {topic} » ?"
    )
    return [
        f"Que faut-il savoir sur « {topic} » ?",
        middle,
        last,
    ]


def enrich_articles(site_dir: Path) -> tuple[int, int, int]:
    """Ajoute un H2 et une FAQ uniquement quand ils sont absents."""
    h2_added = 0
    semantic_h2_added = 0
    faq_added = 0
    history_words = re.compile(r"\b(histoire|siècle|année|autrefois|époque|patrimoine|mémoire)\b", re.I)

    for target in site_dir.rglob("index.html"):
        document = html.parse(str(target))
        articles = document.xpath(
            '//main//article[contains(concat(" ", normalize-space(@class), " "), " feature-story ")]'
            ' | //main/div[contains(concat(" ", normalize-space(@class), " "), " content ")]/article'
            ' | //main//article[contains(concat(" ", normalize-space(@class), " "), " pont-story ")]'
        )
        if not articles:
            continue
        article = articles[0]
        h1 = document.xpath("//h1[1]")
        if not h1:
            continue
        title = clean_text(h1[0])
        topic = short_topic(title)
        destination = str(target.parent.relative_to(site_dir)).replace("\\", "/")

        if not article.xpath(".//h2"):
            heading = html.Element("h2", {"class": "generated-h2"})
            heading.text = generated_h2(destination, topic)
            article.insert(0, heading)
            h2_added += 1

        semantic_h2_added += add_semantic_h2s(article, destination)

        # Les FAQ générées sont recalculées à chaque passe pour suivre un titre
        # corrigé, tandis que les FAQ rédigées manuellement restent intactes.
        previous_generated = document.xpath(
            '//section[contains(concat(" ", normalize-space(@class), " "), " generated-faq ")]'
        )
        for previous in previous_generated:
            parent = previous.getparent()
            if parent is not None:
                parent.remove(previous)

        faq_exists = document.xpath(
            '//*[contains(concat(" ", normalize-space(@class), " "), " faq ")]'
        )
        h2_labels = " ".join(clean_text(node).lower() for node in document.xpath("//h2"))
        if faq_exists or "questions fréquentes" in h2_labels or re.search(r"\bfaq\b", h2_labels):
            target.write_text(
                html.tostring(document, encoding="unicode", method="html", doctype="<!doctype html>"),
                encoding="utf-8",
            )
            continue

        paragraphs = []
        for node in article.xpath(".//p"):
            text = clean_text(node)
            if len(text) >= 70 and not text.startswith(BOILERPLATE_PREFIXES):
                paragraphs.append(text)
        hero_intro = document.xpath('//section[contains(@class,"hero")]//p[1]')
        if not paragraphs and hero_intro:
            paragraphs.append(clean_text(hero_intro[0]))
        if not paragraphs:
            paragraphs.append(f"Cette fiche présente {topic} et les informations disponibles sur ce sujet.")

        first = paragraphs[0]
        middle_candidates = [p for p in paragraphs[1:] if history_words.search(p)] or paragraphs[1:]
        middle = middle_candidates[0] if middle_candidates else first
        practical_candidates = []
        for keyword in ("adresse", "horaire", "tarif", "prix", "parking", "accès", "réserver", "réservation", "ouvert", "ouverture", "venir", "conseil"):
            match = next((p for p in paragraphs if re.search(rf"\b{keyword}\b", p, re.I)), None)
            if match:
                practical_candidates.append(match)
                break
        last = practical_candidates[0] if practical_candidates else paragraphs[-1]
        answers = [first, middle, last]

        faq = html.Element("section", {"class": "faq generated-faq"})
        faq_title = etree.SubElement(faq, "h2")
        faq_title.text = f"Questions fréquentes sur {topic}"
        for question, answer in zip(faq_questions(destination, topic, bool(practical_candidates)), answers):
            qa = etree.SubElement(faq, "div", {"class": "qa"})
            q = etree.SubElement(qa, "h3")
            q.text = question
            a = etree.SubElement(qa, "p")
            a.text = compact_answer(answer)

        container = article.getparent()
        agendas = container.xpath('./section[contains(concat(" ", normalize-space(@class), " "), " agenda ")]')
        if agendas:
            container.insert(container.index(agendas[0]), faq)
        else:
            container.append(faq)
        faq_added += 1
        target.write_text(
            html.tostring(document, encoding="unicode", method="html", doctype="<!doctype html>"),
            encoding="utf-8",
        )
    return h2_added, semantic_h2_added, faq_added


def position_videos_left(site_dir: Path) -> None:
    """Place les vidéos des anciennes fiches conservées dans la colonne média."""
    for target in site_dir.rglob("index.html"):
        document = html.parse(str(target))
        articles = document.xpath(
            '//main/div[contains(concat(" ", normalize-space(@class), " "), " content ")]/article'
            '[.//div[contains(concat(" ", normalize-space(@class), " "), " video ")]]'
        )
        if not articles:
            continue
        article = articles[0]
        container = article.getparent()
        videos = article.xpath(
            './/div[contains(concat(" ", normalize-space(@class), " "), " video ")]'
        )
        if not videos:
            continue
        media = html.Element("aside", {"class": "feature-media"})
        for video in videos:
            media.append(video)
        container.attrib["class"] = "wrap feature-layout"
        article.attrib["class"] = "feature-story"
        container.insert(container.index(article), media)
        target.write_text(
            html.tostring(document, encoding="unicode", method="html", doctype="<!doctype html>"),
            encoding="utf-8",
        )


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
            preserved = read_existing_page(target, destination)
            original = html.fromstring(downloaded[source])
            original_h1 = original.xpath("//h1")
            if original_h1:
                preserved["title"] = clean_text(original_h1[0])
            pages.append(preserved)
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
            known_destinations.add(destination)

    for destination in PRESERVED_ALIASES:
        target = site_dir / destination / "index.html"
        if destination not in known_destinations and target.exists():
            pages.append(read_existing_page(target, destination))
            known_destinations.add(destination)

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
        if "/" in category or category == "autres":
            continue
        label, emoji = label_for(category)
        home_cards.append((category, f"{emoji} {label}", f"{len(cards)} fiche{'s' if len(cards) > 1 else ''} dans cette rubrique."))
    for page in pages:
        if "/" not in page["destination"]:
            home_cards.append(
                (
                    page["destination"],
                    f"📷 {page['title']}",
                    description(page["intro"], page["title"]),
                )
            )
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

    position_videos_left(site_dir)
    synchronized_titles = synchronize_original_titles(site_dir, downloaded)
    h2_added, semantic_h2_added, faq_added = enrich_articles(site_dir)

    print(f"URL découvertes : {len(urls)}")
    print(f"Rubriques détectées : {len(category_sources) - 1}")
    print(f"Fiches téléchargées : {len(downloaded)}")
    print(f"Fiches publiées dans le pilote : {len(pages)}")
    print(f"Vidéos conservées : {sum(int(page.get('videos', 0)) for page in pages)}")
    print(f"Titres synchronisés avec l’original : {synchronized_titles}")
    print(f"H2 ajoutés : {h2_added}")
    print(f"H2 sémantiques ajoutés : {semantic_h2_added}")
    print(f"FAQ ajoutées : {faq_added}")
    print(f"Échecs : {len(failures)}")
    if failures:
        print("\n".join(failures))


if __name__ == "__main__":
    main()

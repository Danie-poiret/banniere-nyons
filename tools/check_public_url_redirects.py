"""Read-only verification of the EHPAD publication, images and navigation."""
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import json, re, time

BASE = "https://www.vivreanyons.fr/"
ARTICLE = BASE + "sante-nyons/ehpad-nyons/"
URLS = [
  "https://www.vivreanyons.fr/sante-nyons/ehpad-nyons/",
  "https://www.vivreanyons.fr/sante-nyons/",
  "https://www.vivreanyons.fr/infos-pratiques-nyons/",
  "https://www.vivreanyons.fr/toutes-les-pages/",
  "https://www.vivreanyons.fr/assets/photos/ehpad-nyons/jardin-et-batiment.png",
  "https://www.vivreanyons.fr/assets/photos/ehpad-nyons/facade-et-balcons.png",
  "https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/ehpad-nyons/",
  "https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/",
  "https://www.vivreanyons.fr/vivreanyons-test/infos-pratiques-nyons/",
  "https://www.vivreanyons.fr/vivreanyons-test/toutes-les-pages/",
  "https://www.vivreanyons.fr/vivreanyons-test/assets/photos/ehpad-nyons/jardin-et-batiment.png",
  "https://www.vivreanyons.fr/vivreanyons-test/assets/photos/ehpad-nyons/facade-et-balcons.png",
  "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/ehpad-nyons/",
  "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/",
  "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/",
  "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/toutes-les-pages/",
  "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/ehpad-nyons/jardin-et-batiment.png",
  "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/ehpad-nyons/facade-et-balcons.png",
  "https://www.vivreanyons.fr/",
  "https://www.vivreanyons.fr/sitemap.xml",
  "https://www.vivreanyons.fr/infos-pratiques-nyons/ccas-nyons/",
  "https://www.vivreanyons.fr/infos-pratiques-nyons/apa-nyons/",
  "https://www.vivreanyons.fr/infos-pratiques-nyons/Alzheimer-Nyons/",
  "https://www.vivreanyons.fr/sante-nyons/teleassistance-nyons/",
  "https://www.vivreanyons.fr/infos-pratiques-nyons/portage-repas-nyons/",
  "https://www.vivreanyons.fr/sante-nyons/kinesitherapeute-nyons/",
"https://www.vivreanyons.fr/infos-pratiques-nyons/plombier-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/infos-pratiques-nyons/plombier-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/plombier-nyons/",
"https://www.vivreanyons.fr/assets/photos/plombier-nyons-meuble-sous-evier.webp",
"https://www.vivreanyons.fr/assets/photos/plombier-nyons-siphon-raccordements.webp",
"https://www.vivreanyons.fr/assets/photos/plombier-nyons-pose-robinetterie.webp",
"https://www.vivreanyons.fr/ou-dormir-a-nyons/villa-des-poete/",
"https://www.vivreanyons.fr/ou-dormir-a-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/ou-dormir-a-nyons/villa-des-poete/",
"https://www.vivreanyons.fr/vivreanyons-test/ou-dormir-a-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/ou-dormir-a-nyons/villa-des-poete/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/ou-dormir-a-nyons/",
"https://www.vivreanyons.fr/assets/photos/437f810cbd2d493dea6a.webp"
]
TITLE = "Maison de retraite et EHPAD à Nyons : tarifs, places, Alzheimer et admission"
class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals, self.robots, self.h1, self.images, self.scripts = [], [], 0, [], []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1": self.h1 += 1
        if tag == "link" and attrs.get("rel") == "canonical": self.canonicals.append(attrs.get("href"))
        if tag == "meta" and attrs.get("name") == "robots": self.robots.append(attrs.get("content"))
        if tag == "img": self.images.append(attrs)
        if tag == "script" and attrs.get("src"): self.scripts.append(attrs["src"])

def check(url):
    result = {"requested": url}
    try:
        with urlopen(Request(url, headers={"User-Agent":"VivreAnyons-Publication-Verification/1.0"}), timeout=25) as response:
            data = response.read(2000000)
            result.update(status=response.status, final=response.geturl(), contentType=response.headers.get("Content-Type"))
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            result.update(pngSignature=True, width=int.from_bytes(data[16:20],"big"), height=int.from_bytes(data[20:24],"big"))
            expected = (462,446) if "jardin-et-batiment" in url else (312,210)
            result["correctDimensions"] = (result["width"],result["height"]) == expected
            return result
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            result["webpSignature"] = True
            result["imageNotEmpty"] = len(data) > 100
            return result
        source = data.decode("utf-8")
        if url.endswith("/sitemap.xml"):
            result["newArticleLast"] = re.findall(r"<loc>(.*?)</loc>", source)[-1] == ARTICLE
            return result
        page = Page()
        page.feed(source)
        result.update(canonical=page.canonicals,robots=page.robots)
        if "/sante-nyons/ehpad-nyons/" in url:
            graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',source,re.S).group(1))["@graph"]
            article = next(g for g in graph if g["@type"]=="Article")
            faq = next(g for g in graph if g["@type"]=="FAQPage")
            result["correctTitle"] = "<h1>"+TITLE+"</h1>" in source and page.h1 == 1
            result["tables5"] = source.count('<table class="ehpad-table">') == 5
            result["faq8"] = source.count('<div class="qa">') == 8 and len(faq["mainEntity"]) == 8
            result["publicationDate"] = article["datePublished"] == "2026-10-08" and article["dateModified"] == "2026-10-08"
            result["photos2"] = sum("assets/photos/ehpad-nyons/" in i.get("src","") for i in page.images) == 2 and len(article["image"]) == 2
            result["imageMetadata"] = all(i.get("width") and i.get("height") and i.get("alt") for i in page.images if "/ehpad-nyons/" in i.get("src",""))
            result["responsiveTables"] = "max-width:100%;overflow-x:auto" in source and source.count('tabindex="0"') == 5 and ".feature-story{min-width:0}" in source
            result["datedPrices"] = all(t in source for t in ["2 362,20 €","2 421,60 €","29 avril 2026","25 juin 2025","30 jours"])
            result["ashTariffDifference"] = all(t in source for t in ["93,62 €/jour","89,92 €/jour","tarif hébergement ASH diffère"])
            result["capacityQualified"] = "Ces indications ne concordent pas" in source and "76 places libres" in source
            result["aidsQualified"] = "récupérée, notamment sur la succession" in source and "cumulées sous conditions" in source
            result["residenceClosed"] = "fermé définitivement à la fin du mois de juin 2025" in source and 'id="residence-pousterle-fermee"' in source
            result["activeEHPADSeparate"] = "L’EHPAD reste référencé dans le portail national" in source
            result["escapadeMoved"] = '<th scope="row">Escapade, soutien aux aidants</th><td>Moun Oustaou, 6 rue Ferdinand Vigne</td>' in source and "située à La Pousterle" not in source
            result["mounContact"] = 'href="tel:+33475266565"' in source and "centre de ressources territorial" in source
            result["municipalObsolescence"] = "Cette partie est obsolète" in source and "comprend également, séparément" not in source
            result["admission"] = "https://trajectoire.sante-ra.fr/" in source and "dossier national unique" in source
            result["readerQuestions"] = 'id="lecteurs"' in source and "Questions aux lecteurs" in source
            result["sources"] = "Sources et liens utiles" in source and "Informations vérifiées le 8 octobre 2026" in source
            result["canonicalCorrect"] = page.canonicals == [ARTICLE]
            mirror = "/vivreanyons-test/" in url
            result["robotsCorrect"] = page.robots == (["noindex,nofollow"] if mirror else ["index,follow"])
            prefix = "banniere-nyons/vivreanyons-test/" if "/banniere-nyons/" in url else ("vivreanyons-test/" if mirror else "")
            result["imagePaths"] = all(i.get("src","").startswith("/"+prefix+"assets/photos/ehpad-nyons/") for i in page.images if "ehpad-nyons" in i.get("src",""))
            result["sharedMenuAndScript"] = 'data-nyons-shortcut="hebergement"' in source and 'data-weather-nav="direct"' in source and any("google-analytics-20261008-v1" in s for s in page.scripts)
        if "/infos-pratiques-nyons/plombier-nyons/" in url:
            result["plombierUpdated"] = 'data-plomberie-updated="2026-10-08"' in source
            result["plombierTitle"] = "<h1>Plombier à Nyons : dépannage, fuite d’eau, chauffe-eau et contacts</h1>" in source and page.h1 == 1
            result["plombierDates"] = '"datePublished":"2026-10-04"' in source and '"dateModified":"2026-10-08"' in source
            result["plombierTables5"] = source.count('<div class="plomberie-table" role="region"') == 5
            result["plombierFAQ12"] = source.count('<div class="qa">') == 12
            schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)]
            faq = next(s for s in schemas if s.get("@type")=="FAQPage")
            result["plombierSchema12"] = len(faq["mainEntity"]) == 12
            result["plombierPhotosPreserved"] = all(p in source for p in ["plombier-nyons-meuble-sous-evier.webp","plombier-nyons-siphon-raccordements.webp","plombier-nyons-pose-robinetterie.webp"])
            result["plombierDimensions"] = all(t in source for t in ['width="235" height="182"','width="145" height="137"','width="165" height="113"'])
            result["plombierContacts"] = all(n in source for n in ["04 75 26 00 08","04 75 26 11 12","06 40 11 55 64","04 75 26 01 81","07 69 11 82 77","04 75 26 03 50","04 75 27 74 01"])
            result["plombierCallLinks"] = all(n in source for n in ['href="tel:+33475260008"','href="tel:+33640115564"','href="tel:+33475277401"'])
            result["plombierSafety"] = "ne manipule pas les appareils, prises ou câbles" in source and "zone humide" in source
            result["plombierDevis"] = "avant intervention dès le premier euro" in source and "ce ne sont pas des tarifs moyens à Nyons" in source
            result["plombierOldAdvice"] = all(t in source for t in ["Remplacer un meuble sous évier","Filtre, antitartre ou traitement de l’eau","Faure est apprécié pour son sérieux","Morin plaît pour son efficacité"])
            result["plombierFAQPreserved"] = all(q in source for q in ["Quels avis retenir pour choisir un artisan ?","Que préparer avant de faire remplacer le meuble ?","Peut-on appeler une entreprise des communes voisines ?"])
            result["plombierClean"] = "Texte collé" not in source and "Ta fiche précédente" not in source
            result["plombierSources"] = "Sources et liens utiles" in source and "Questions aux lecteurs" in source
            result["plombierCanonical"] = page.canonicals == [BASE+"infos-pratiques-nyons/plombier-nyons/"]
            result["plombierMenus"] = 'data-nyons-shortcut="hebergement"' in source and 'data-weather-nav="direct"' in source and any("google-analytics-20261008-v1" in s for s in page.scripts)
        if "/ou-dormir-a-nyons/villa-des-poete/" in url:
            result["villaUpdated"] = 'data-villa-updated="2026-10-08"' in source
            result["villaTitle"] = "<h1>Villa des Poètes à Nyons : avis, tarifs, piscine et réservation</h1>" in source and page.h1 == 1
            graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',source,re.S).group(1))["@graph"]
            article = next(g for g in graph if g["@type"]=="Article")
            faq = next(g for g in graph if g["@type"]=="FAQPage")
            result["villaNoInventedPublicationDate"] = "datePublished" not in source and article["dateModified"] == "2026-10-08"
            result["villaFAQ8"] = len(faq["mainEntity"]) == 8 and source.count('<div class="qa">') == 8
            result["villaOldFAQPreserved"] = all(t in source for t in ["La Villa des Poètes est-elle dans le centre de Nyons ?","La Villa des Poètes accueille-t-elle des séjours en hiver ?"])
            result["villaTables3"] = source.count('<table class="villa-table">') == 3 and source.count('tabindex="0"') == 3
            result["villaPhotoPreserved"] = "437f810cbd2d493dea6a.webp" in source and 'width="445" height="286"' in source and len(page.images) == 1
            result["villaPriceGrid"] = all(t in source for t in ["80 €","90 €","95 €","0,80 €","25 €","10 %","50 %","30 %"])
            result["villaRooms"] = all(t in source for t in ["La Bellissima","L’Azzurra","Le Cabanon","L’Estivale","Baignoire et WC","Du 1er mai au 30 septembre"])
            result["villaPoolQualified"] = "11 × 5 mètres" in source and "piscine extérieure saisonnière" in source
            result["villaDirectContacts"] = 'href="tel:+33645222205"' in source and 'href="mailto:info@lavilladespoetes.fr"' in source
            result["villaPractical"] = all(t in source for t in ["17 h et 19 h","11 h","531 chemin de Bellevue","Les animaux ne sont pas acceptés","parking privé"])
            result["villaRatingsDated"] = "9,2/10 pour 13 évaluations" in source and "4,9/5 pour 76 avis" in source and "8 octobre 2026" in source
            result["villaReviewsPreserved"] = all(t in source for t in ["leur propreté et leur confort","sans être envahissants","dernier tronçon monte","je n’ai jamais dormi"])
            result["villaClean"] = "Philippe" not in source and "Eric" not in source and "Lydia" not in source and "terrain de pétanque" not in source
            result["villaSourcesAndReaders"] = "Sources et liens utiles" in source and "Questions aux lecteurs" in source
            result["villaCanonical"] = page.canonicals == [BASE+"ou-dormir-a-nyons/villa-des-poete/"]
            result["villaRobots"] = page.robots == (["noindex,nofollow"] if "/vivreanyons-test/" in url else ["index,follow"])
            result["villaMenuAndScript"] = 'data-nyons-shortcut="hebergement"' in source and 'data-weather-nav="direct"' in source and any("google-analytics-20261008-v1" in s for s in page.scripts)
        if url.endswith("/ou-dormir-a-nyons/") or url.endswith("/toutes-les-pages/"):
            result["villaIndexUpdated"] = "Villa des Poètes à Nyons : avis, tarifs, piscine et réservation" in source and "chambres d’hôtes à 4 km du centre" in source
        if url.endswith("/sante-nyons/"):
            g = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',source,re.S).group(1))["@graph"]
            items = next(g for g in g if g["@type"]=="ItemList")
            result["healthList30"] = items["numberOfItems"] == 30 and len(items["itemListElement"]) == 30
            result["healthNewCard"] = "data-ehpad-card" in source and any(i["url"]==ARTICLE for i in items["itemListElement"])
        if url.endswith("/infos-pratiques-nyons/") or url.endswith("/toutes-les-pages/"):
            result["plombierIndexTitle"] = "Plombier à Nyons : dépannage, fuite d’eau, chauffe-eau et contacts" in source
            result["newCard"] = "data-ehpad-card" in source and "sante-nyons/ehpad-nyons/" in source
        if url == BASE:
            result["latestEHPAD"] = TITLE in source and "sante-nyons/ehpad-nyons/" in source
            result["weatherPreserved"] = "weather" in source and "meteo-nyons/" in source
            result["lodgingMenuPreserved"] = 'data-nyons-shortcut="hebergement"' in source
    except Exception as error:
        result["error"] = str(error)
    return result

for attempt in range(12):
    ready = check(BASE+"ou-dormir-a-nyons/villa-des-poete/")
    home = check(BASE)
    mirror_ready = check(BASE+"vivreanyons-test/ou-dormir-a-nyons/villa-des-poete/")
    second_mirror_ready = check(BASE+"banniere-nyons/vivreanyons-test/ou-dormir-a-nyons/villa-des-poete/")
    if ready.get("villaUpdated") and home.get("latestEHPAD") and mirror_ready.get("villaCanonical") and second_mirror_ready.get("villaCanonical"):
        break
    print("Waiting for Villa des Poètes and preserved homepage", attempt+1, flush=True)
    time.sleep(10)
with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(check, URLS))
print("PUBLIC_URL_AUDIT_BEGIN")
print(json.dumps({"checkedDate":"2026-10-08","readOnly":True,"results":results},ensure_ascii=False,indent=2))
print("PUBLIC_URL_AUDIT_END")
failures = [r for r in results if r.get("status") != 200 or r.get("error") or any(v is False for v in r.values())]
if failures:
    raise SystemExit("Public checks failed: "+json.dumps(failures,ensure_ascii=False))

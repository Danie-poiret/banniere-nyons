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
"https://www.vivreanyons.fr/assets/photos/plombier-nyons-pose-robinetterie.webp"
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
        if url.endswith("/sante-nyons/"):
            g = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',source,re.S).group(1))["@graph"]
            items = next(g for g in g if g["@type"]=="ItemList")
            result["healthList30"] = items["numberOfItems"] == 30 and len(items["itemListElement"]) == 30
            result["healthNewCard"] = "data-ehpad-card" in source and any(i["url"]==ARTICLE for i in items["itemListElement"])
        if url.endswith("/infos-pratiques-nyons/") or url.endswith("/toutes-les-pages/"):
            result["plombierIndexTitle"] = "${load("plombierDraft").title}" in source
            result["newCard"] = "data-ehpad-card" in source and "sante-nyons/ehpad-nyons/" in source
        if url == BASE:
            result["latestEHPAD"] = TITLE in source and "sante-nyons/ehpad-nyons/" in source
            result["weatherPreserved"] = "weather" in source and "meteo-nyons/" in source
            result["lodgingMenuPreserved"] = 'data-nyons-shortcut="hebergement"' in source
    except Exception as error:
        result["error"] = str(error)
    return result

for attempt in range(12):
    ready = check(BASE+"infos-pratiques-nyons/plombier-nyons/")
    home = check(BASE)
    if ready.get("plombierUpdated") and home.get("latestEHPAD"):
        break
    print("Waiting for the improved plumbing article and preserved homepage", attempt+1, flush=True)
    time.sleep(10)
with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(check, URLS))
print("PUBLIC_URL_AUDIT_BEGIN")
print(json.dumps({"checkedDate":"2026-10-08","readOnly":True,"results":results},ensure_ascii=False,indent=2))
print("PUBLIC_URL_AUDIT_END")
failures = [r for r in results if r.get("status") != 200 or r.get("error") or any(v is False for v in r.values())]
if failures:
    raise SystemExit("Public checks failed: "+json.dumps(failures,ensure_ascii=False))

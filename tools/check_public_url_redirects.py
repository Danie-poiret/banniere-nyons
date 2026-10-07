"""Read-only checks of public URLs and the Maison de Santé article."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError

URLS = [
"https://www.vivreanyons.fr/sante-nyons/maison-de-sante-nyons/",
"https://www.vivreanyons.fr/assets/photos/668de5d6a91a56f4b265.webp",
"https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/maison-de-sante-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/668de5d6a91a56f4b265.webp",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/maison-de-sante-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/668de5d6a91a56f4b265.webp",
"https://www.vivreanyons.fr/sante-nyons/radiologie-nyons/",
"https://www.vivreanyons.fr/assets/photos/radiologie-nyons/radiographies-os-et-thorax.png",
"https://www.vivreanyons.fr/assets/photos/radiologie-nyons/lecture-radiographie-thorax.png",
"https://www.vivreanyons.fr/assets/photos/radiologie-nyons/images-cerebrales-ecran.png",
"https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/radiologie-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/radiologie-nyons/radiographies-os-et-thorax.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/radiologie-nyons/lecture-radiographie-thorax.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/radiologie-nyons/images-cerebrales-ecran.png",
"https://www.vivreanyons.fr/vivreanyons-test/",
"https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/radiologie-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/radiologie-nyons/radiographies-os-et-thorax.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/radiologie-nyons/lecture-radiographie-thorax.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/radiologie-nyons/images-cerebrales-ecran.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/",
"https://www.vivreanyons.fr/sante-nyons/laboratoire-nyons/",
"https://www.vivreanyons.fr/assets/photos/laboratoire-nyons/prise-de-sang-au-laboratoire.png",
"https://www.vivreanyons.fr/assets/photos/laboratoire-nyons/tubes-et-resultats-analyses.png",
"https://www.vivreanyons.fr/assets/photos/laboratoire-nyons/prelevement-sanguin-et-tubes.png",

"https://www.vivreanyons.fr/sante-nyons/",
"https://www.vivreanyons.fr/infos-pratiques-nyons/Alzheimer-Nyons/",
"https://www.vivreanyons.fr/infos-pratiques-nyons/nyons-sante/",
"https://www.vivreanyons.fr/infos-pratiques-nyons/services-de-livraison-nyons/",
"https://www.vivreanyons.fr/questions-utiles-nyons/Dentiste-Nyons/",
"https://www.vivreanyons.fr/sante-nyons/audioprothesiste-nyons/",
"https://www.vivreanyons.fr/assets/photos/audioprothesiste-nyons/appareil-auditif-contour-oreille.png",
"https://www.vivreanyons.fr/assets/photos/audioprothesiste-nyons/examen-oreille-otoscope.png",
"https://www.vivreanyons.fr/assets/photos/audioprothesiste-nyons/mise-en-place-aide-auditive.png",
"https://www.vivreanyons.fr/",
"https://www.vivreanyons.fr/Auvergne-Rhone-Alpes/Drome/Piscine-de-Pierrelatte/",
"https://www.vivreanyons.fr/evenements-nyons/",
"https://www.vivreanyons.fr/Provence-Alpes-Cote-dAzur/Auvergne-Rhone-Alpes/Drome/Piscine-de-Pierrelatte",
"https://www.vivreanyons.fr/evenements-",
"https://www.vivreanyons.fr/naLogImpressions",
"https://drome.vivreanyons.fr/evenements/",
"https://www.vivreanyons.fr/video-nyons/piscine-de-nyons",
"https://www.vivreanyons.fr/a-faire-autour-de-Nyons/se-baigner-au-pas-des-ondes",
"https://www.vivreanyons.fr/video-nyons/bourse-nyons",
"https://drome.vivreanyons.fr/",
"https://www.vivreanyons.fr/que-faire-nyons/Huilerie-Richard-Nyons",
"http://www.vivreanyons.fr/",
"http://vivreanyons.fr/",
"https://www.vivreanyons.fr/ou-dormir-a-nyons/capfun-de-nyons",
"https://www.vivreanyons.fr/restaurants-de-nyons/Restaurant-alicoque-Nyons",
"https://www.vivreanyons.fr/que-faire-autour-de-nyons/village-de-venterol/",
"https://www.vivreanyons.fr/a-faire-autour-de-Nyons/village-de-venterol/",
]

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonicals, self.robots, self.refresh = [], [], None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href"))
        if tag == "meta" and attrs.get("name", "").lower() in {"robots", "googlebot"}:
            self.robots.append(attrs.get("content"))
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
            self.refresh = attrs.get("content")

def check(url):
    chain = []
    class Trace(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            chain.append({"from": req.full_url, "status": code, "to": newurl})
            if len(chain) > 8:
                raise HTTPError(req.full_url, 508, "Redirect chain too long", headers, fp)
            return super().redirect_request(req, fp, code, msg, headers, newurl)
    result = {"requested": url}
    try:
        opener = build_opener(Trace())
        req = Request(url, headers={"User-Agent": "VivreAnyons-URL-Verification/1.0", "Accept": "text/html"})
        with opener.open(req, timeout=15) as response:
            result.update({
                "final": response.geturl(),
                "status": response.status,
                "chain": chain,
                "server": response.headers.get("Server"),
                "xRobotsTag": response.headers.get("X-Robots-Tag"),
                "contentType": response.headers.get("Content-Type"),
            })
            data = response.read(2000000)
            if response.headers.get("Content-Type", "").startswith("image/png"):
                result["pngSignature"] = data[:8] == b"\x89PNG\r\n\x1a\n"
                result["width"] = int.from_bytes(data[16:20], "big")
                result["height"] = int.from_bytes(data[20:24], "big")
                return result
            if response.headers.get("Content-Type", "").startswith("image/webp"):
                result["webpSignature"] = data[:4] == b"RIFF" and data[8:12] == b"WEBP"
                result["bytes"] = len(data)
                if data[12:16] == b"VP8 ":
                    result["width"] = int.from_bytes(data[26:28], "little") & 16383
                    result["height"] = int.from_bytes(data[28:30], "little") & 16383
                return result
            source = data.decode("utf-8", errors="replace")
        page = Page()
        page.feed(source)
        result.update({"canonicals": page.canonicals, "robots": page.robots, "metaRefresh": page.refresh})
        if any(slug in url for slug in ["audioprothesiste-nyons", "Dentiste-Nyons", "nyons-sante", "services-de-livraison-nyons", "Alzheimer-Nyons", "sante-nyons/"]) or url == "https://www.vivreanyons.fr/":
            result["hearingArticleLinked"] = "/sante-nyons/audioprothesiste-nyons/" in source
            result["hearingImageLinked"] = "/assets/photos/audioprothesiste-nyons/appareil-auditif-contour-oreille.png" in source
            result["hearingPhotosLinked"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/audioprothesiste-nyons/[^"]+)"', source)
            result["svgRoot"] = "<svg" in source
            result["headings"] = re.findall(r"<h1[^>]*>(.*?)</h1>", source, re.S)
        if url == "https://www.vivreanyons.fr/":
            result["latestMaisonSanteArticle"] = 'data-latest-article="/sante-nyons/maison-de-sante-nyons/"' in source
            result["maisonSanteHomepagePhoto"] = "/assets/photos/668de5d6a91a56f4b265.webp" in source
        if "/sante-nyons/laboratoire-nyons/" in url:
            result["labPhone"] = 'href="tel:+33475262677"' in source
            result["labAddress"] = "26 avenue Paul Laurens" in source
            result["labPhotos"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/laboratoire-nyons/[^"]+)"', source)
            result["hbA1cQualification"] = "ne nécessite pas, à elle seule, d’être à jeun" in source
            result["editorialHeadings"] = len(re.findall(r"<h2", source))
        if url == "https://www.vivreanyons.fr/sante-nyons/":
            result["laboratoryLinked"] = 'href="/sante-nyons/laboratoire-nyons/"' in source
            result["alzheimerLinked"] = 'href="/infos-pratiques-nyons/Alzheimer-Nyons/"' in source
            result["alzheimerNavigation"] = 'href="#memoire-aidants"' in source
            result["alzheimerSection"] = 'id="memoire-aidants"' in source
            result["healthItems25"] = '"numberOfItems":25' in source
        if "Alzheimer-Nyons" in url:
            result["healthBackLink"] = "data-health-back-link" in source
            result["originalPhoto"] = "/assets/photos/7e9287ac607cf945800d.webp" in source
        if "/nyons-sante/" in url:
            result["photos"] = re.findall(r'<img[^>]+src="([^"]+)"', source)
            result["atmoLinked"] = "atmo-auvergnerhonealpes.fr/air-commune/Ville/26220/previsions" in source
            result["pollens"] = "Les graminées, l’olivier ou l’ambroisie" in source
            result["noCurePromise"] = all(text not in source for text in ["Ce n’est pas une impression", "L’air y est extrêmement propre", "réduisent quasiment tous"])
            result["updated"] = 'datetime="2026-10-07"' in source
        if "/services-de-livraison-nyons/" in url:
            result["photos"] = re.findall(r'<img[^>]+src="([^"]+)"', source)
            result["ccasContact"] = 'href="tel:+33475265027"' in source
            result["intermarcheContact"] = 'href="tel:+33475261968"' in source
            result["ccbdpContact"] = 'href="tel:+33475269075"' in source
            result["hours"] = "entre 7 h 30 et 11 h 30" in source
            result["oldTariffRemoved"] = all(text not in source for text in ["8,80", "10,30"])
            result["updated"] = 'datetime="2026-10-07"' in source
        if "Dentiste-Nyons" in url:
            result["dentistDirectoryLinked"] = 'href="/infos-pratiques-nyons/dentistes-nyons/"' in source
            result["consultation23"] = "<strong>23 €</strong>" in source
            result["repayment1380"] = "<strong>13,80 €</strong>" in source
            result["mtDents"] = "M’T dents tous les ans !" in source
            result["photoPreserved"] = "/assets/photos/a4856b24e55c3e43021b.webp" in source
            result["updated"] = 'datetime="2026-10-07"' in source
        if url in ["https://www.vivreanyons.fr/","https://www.vivreanyons.fr/vivreanyons-test/","https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/"]:
            result["maisonSanteFeatured"] = bool(re.search(r'data-latest-article="[^"]*sante-nyons/maison-de-sante-nyons/"', source))
            result["maisonSanteHomepagePhoto"] = "assets/photos/668de5d6a91a56f4b265.webp" in source
        if url in ["https://www.vivreanyons.fr/sante-nyons/","https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/","https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/"]:
            result["radiologyLinked"] = bool(re.search(r'href="[^"]*sante-nyons/radiologie-nyons/"', source))
            result["healthItems25"] = '"numberOfItems":25' in source
            result["alzheimerPresent"] = "Alzheimer-Nyons/" in source and 'id="memoire-aidants"' in source
        if "/sante-nyons/radiologie-nyons/" in url:
            result["radioPhone"] = 'href="tel:+33475265200"' in source and 'href="tel:+33475265276"' in source
            result["radioAddress"] = "11 avenue Jules Bernard" in source
            result["radioPhotos"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/radiologie-nyons/[^"]+)"', source)
            result["photoCaptions"] = len(re.findall(r"<figcaption>", source))
            result["headings"] = re.findall(r"<h1[^>]*>(.*?)</h1>", source, re.S)
            result["editorialHeadings"] = len(re.findall(r"<h2", source))
            result["appointment"] = "<strong>sur rendez-vous</strong>" in source
            result["equipmentQualified"] = "ne mentionnent ni scanner ni IRM sur le site de Nyons" in source
            result["papyPreserved"] = "Le petit conseil de Papy avant votre rendez-vous" in source
            result["publishDate"] = '"datePublished":"2026-10-07"' in source
        if url in ["https://www.vivreanyons.fr/sante-nyons/","https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/","https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/"]:
            result["maisonSanteLinked"] = bool(re.search(r'href="[^"]*sante-nyons/maison-de-sante-nyons/"', source))
        if "/sante-nyons/maison-de-sante-nyons/" in url:
            result["address"] = "21 rue Émile Lisbonne" in source
            result["phoneContacts"] = all('href="tel:' + phone + '"' in source for phone in ["+33487120003","+33475260833","+33475262442","+33475268502","+33767175054","+33955184952","+33475270022","+33475460597"])
            result["psychologistAddressQualified"] = "10 avenue Jules Bernard à Nyons" in source and "plutôt que de vous rendre automatiquement rue Émile Lisbonne" in source
            result["podologistCareQualified"] = "les soins de pédicurie sont annoncés pour les patients déjà connus" in source
            result["rentCausalityQualified"] = "ne permet pas de mesurer les départs de praticiens ni d’en attribuer la cause aux loyers" in source
            result["papyTone"] = "Le conseil de Papy" in source
            result["noSocialNames"] = all(name not in source for name in ["Luca Giuliani", "Liliane Sauceau", "Danielle Nicolas", "Nyons : 5 élus"])
            result["photoCaption"] = "Photo d’illustration." in source
            result["headings"] = re.findall(r"<h1[^>]*>(.*?)</h1>", source, re.S)
            result["editorialHeadings"] = len(re.findall(r"<h2", source))
            result["publishDate"] = '"datePublished":"2026-10-07"' in source
        if page.refresh:
            match = re.search(r"^\s*0\s*;\s*url\s*=\s*(.+?)\s*$", page.refresh, re.I)
            if match:
                result["instantRefreshDestination"] = urljoin(result["final"], match.group(1).strip("\"'"))
    except HTTPError as error:
        result.update({"status": error.code, "final": error.geturl(), "chain": chain, "error": str(error)})
    except Exception as error:
        result.update({"status": None, "chain": chain, "error": str(error)})
    return result

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(check, URLS))
print("PUBLIC_URL_AUDIT_BEGIN")
print(json.dumps({"checkedDate": "2026-10-07", "readOnly": True, "results": results}, ensure_ascii=False, indent=2))
print("PUBLIC_URL_AUDIT_END")

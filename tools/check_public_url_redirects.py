"""Read-only checks of published articles, photographs and site links."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
import time
import re
from urllib.parse import urljoin
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError

URLS = [
"https://www.vivreanyons.fr/que-faire-nyons/promenade-de-la-digue-nyons/",
"https://www.vivreanyons.fr/assets/photos/894fb5e0cf722fa9c603.webp",
"https://www.vivreanyons.fr/que-faire-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/que-faire-nyons/promenade-de-la-digue-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/894fb5e0cf722fa9c603.webp",
"https://www.vivreanyons.fr/vivreanyons-test/que-faire-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/que-faire-nyons/promenade-de-la-digue-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/894fb5e0cf722fa9c603.webp",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/que-faire-nyons/",
"https://www.vivreanyons.fr/sante-nyons/teleassistance-nyons/",
"https://www.vivreanyons.fr/assets/photos/teleassistance-nyons/bouton-bracelet.png",
"https://www.vivreanyons.fr/assets/photos/teleassistance-nyons/montre-sos.png",
"https://www.vivreanyons.fr/assets/photos/teleassistance-nyons/pendentif-alerte.png",
"https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/teleassistance-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/teleassistance-nyons/bouton-bracelet.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/teleassistance-nyons/montre-sos.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/teleassistance-nyons/pendentif-alerte.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/teleassistance-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/teleassistance-nyons/bouton-bracelet.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/teleassistance-nyons/montre-sos.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/teleassistance-nyons/pendentif-alerte.png",
"https://www.vivreanyons.fr/infos-pratiques-nyons/marches-autour-nyons-50-km/",
"https://www.vivreanyons.fr/vivreanyons-test/infos-pratiques-nyons/marches-autour-nyons-50-km/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/marches-autour-nyons-50-km/",
"https://www.vivreanyons.fr/a-faire-autour-de-Nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/a-faire-autour-de-Nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/a-faire-autour-de-Nyons/",
"https://www.vivreanyons.fr/infos-pratiques-nyons/marche-vaison-la-romaine/",
"https://www.vivreanyons.fr/assets/photos/marche-vaison-la-romaine/etal-marche.png",
"https://www.vivreanyons.fr/assets/photos/marche-vaison-la-romaine/paniers-colores.png",
"https://www.vivreanyons.fr/assets/photos/marche-vaison-la-romaine/allees-animees.png",
"https://www.vivreanyons.fr/assets/photos/marche-vaison-la-romaine/vaisselle-marche.png",
"https://www.vivreanyons.fr/assets/photos/marche-vaison-la-romaine/vaison-ville-haute.png",
"https://www.vivreanyons.fr/vivreanyons-test/infos-pratiques-nyons/marche-vaison-la-romaine/",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/marche-vaison-la-romaine/etal-marche.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/marche-vaison-la-romaine/paniers-colores.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/marche-vaison-la-romaine/allees-animees.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/marche-vaison-la-romaine/vaisselle-marche.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/marche-vaison-la-romaine/vaison-ville-haute.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/marche-vaison-la-romaine/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/marche-vaison-la-romaine/etal-marche.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/marche-vaison-la-romaine/paniers-colores.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/marche-vaison-la-romaine/allees-animees.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/marche-vaison-la-romaine/vaisselle-marche.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/marche-vaison-la-romaine/vaison-ville-haute.png",
"https://www.vivreanyons.fr/sante-nyons/kinesitherapeute-nyons/",
"https://www.vivreanyons.fr/assets/photos/kinesitherapeute-nyons/soins-du-dos.png",
"https://www.vivreanyons.fr/assets/photos/kinesitherapeute-nyons/reeducation-genou.png",
"https://www.vivreanyons.fr/assets/photos/kinesitherapeute-nyons/mobilisation-jambe.png",
"https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/kinesitherapeute-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/kinesitherapeute-nyons/soins-du-dos.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/kinesitherapeute-nyons/reeducation-genou.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/kinesitherapeute-nyons/mobilisation-jambe.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/kinesitherapeute-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/kinesitherapeute-nyons/soins-du-dos.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/kinesitherapeute-nyons/reeducation-genou.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/kinesitherapeute-nyons/mobilisation-jambe.png",
"https://www.vivreanyons.fr/infos-pratiques-nyons/apa-nyons/",
"https://www.vivreanyons.fr/assets/photos/apa-nyons/apa-a-domicile.png",
"https://www.vivreanyons.fr/vivreanyons-test/infos-pratiques-nyons/apa-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/apa-nyons/apa-a-domicile.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/apa-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/apa-nyons/apa-a-domicile.png",
"https://www.vivreanyons.fr/infos-pratiques-nyons/dechetterie-nyons/",
"https://www.vivreanyons.fr/assets/photos/dechetterie-nyons/panneau-dechetterie.png",
"https://www.vivreanyons.fr/assets/photos/dechetterie-nyons/bennes-de-tri.png",
"https://www.vivreanyons.fr/vivreanyons-test/infos-pratiques-nyons/dechetterie-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/dechetterie-nyons/panneau-dechetterie.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/dechetterie-nyons/bennes-de-tri.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/dechetterie-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/dechetterie-nyons/panneau-dechetterie.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/dechetterie-nyons/bennes-de-tri.png",
"https://www.vivreanyons.fr/que-faire-nyons/les-vieux-moulins/",
"https://www.vivreanyons.fr/vivreanyons-test/que-faire-nyons/les-vieux-moulins/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/que-faire-nyons/les-vieux-moulins/",
"https://www.vivreanyons.fr/assets/photos/fiche-2038b7f67c32d62b528b.webp",
"https://www.vivreanyons.fr/assets/photos/fiche-21a4b36d1f94e4afe471.webp",
"https://www.vivreanyons.fr/infos-pratiques-nyons/portage-repas-nyons/",
"https://www.vivreanyons.fr/assets/photos/portage-repas-nyons/repas-servi-a-domicile.png",
"https://www.vivreanyons.fr/assets/photos/portage-repas-nyons/tournee-livraison-repas.png",
"https://www.vivreanyons.fr/assets/photos/portage-repas-nyons/plateau-repas-senior.png",
"https://www.vivreanyons.fr/infos-pratiques-nyons/",
"https://www.vivreanyons.fr/toutes-les-pages/",
"https://www.vivreanyons.fr/vivreanyons-test/infos-pratiques-nyons/portage-repas-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/portage-repas-nyons/repas-servi-a-domicile.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/portage-repas-nyons/tournee-livraison-repas.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/portage-repas-nyons/plateau-repas-senior.png",
"https://www.vivreanyons.fr/vivreanyons-test/infos-pratiques-nyons/",
"https://www.vivreanyons.fr/vivreanyons-test/toutes-les-pages/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/portage-repas-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/portage-repas-nyons/repas-servi-a-domicile.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/portage-repas-nyons/tournee-livraison-repas.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/portage-repas-nyons/plateau-repas-senior.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/toutes-les-pages/",
"https://www.vivreanyons.fr/assets/photos/maison-de-sante-nyons/maison-de-sante-nyons-vue-ensemble.png",
"https://www.vivreanyons.fr/assets/photos/maison-de-sante-nyons/maison-de-sante-nyons-facade.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/maison-de-sante-nyons/maison-de-sante-nyons-vue-ensemble.png",
"https://www.vivreanyons.fr/vivreanyons-test/assets/photos/maison-de-sante-nyons/maison-de-sante-nyons-facade.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/maison-de-sante-nyons/maison-de-sante-nyons-vue-ensemble.png",
"https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/assets/photos/maison-de-sante-nyons/maison-de-sante-nyons-facade.png",
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
        if "/infos-pratiques-nyons/marches-autour-nyons-50-km/" in url:
            result["marketsVaisonSummary"] = 'id="vaison-en-detail"' in source and "450 exposants" in source
            result["marketsVaisonLink"] = bool(re.search(r'<a href="[^"]*/infos-pratiques-nyons/marche-vaison-la-romaine/">Découvrir le marché de Vaison-la-Romaine', source))
            result["marketsVaisonLinkCount"] = len(re.findall(r'href="[^"]*/infos-pratiques-nyons/marche-vaison-la-romaine/"', source))
            vaison_rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", source, re.S) if '<th scope="row">Vaison-la-Romaine<' in row]
            result["marketsVaisonRowLinks"] = len(vaison_rows) == 2 and all(re.search(r'<a class="market-source" href="[^"]*/infos-pratiques-nyons/marche-vaison-la-romaine/">Renseignements', row) for row in vaison_rows)
            result["marketsVaisonTripLinks"] = len(vaison_rows) == 2 and all('https://www.bonnesroutes.com/distance/nyons/vaison-la-romaine/' in row for row in vaison_rows)
            result["marketsVaisonHours"] = "<strong>8 h 30–13 h</strong>" in source
            result["marketsOriginalPublicationDate"] = '"datePublished": "2026-10-06"' in source
            result["marketsUpdatedDate"] = '"dateModified": "2026-10-08"' in source
            result["marketsOriginalValreasSummary"] = 'id="valreas-en-detail"' in source
        if "/que-faire-nyons/promenade-de-la-digue-nyons/" in url:
            result["digueUpdated"] = 'data-digue-updated="2026-10-08"' in source
            result["digueTitle"] = "Promenade de la Digue à Nyons : balade facile en famille au bord de l’Eygues" in source
            result["diguePhotoPreserved"] = '/assets/photos/894fb5e0cf722fa9c603.webp' in source and 'width="416" height="234"' in source
            result["digueVideoPreserved"] = 'data-src="https://www.youtube-nocookie.com/embed/0xqG1XybPvI"' in source and 'data-privacy-category="videos"' in source and 'data-privacy-placeholder="videos"' in source
            result["digueOldTextRemoved"] = not any(text in source for text in ["Mamie y va en claquettes", "3 minutes chrono", "J’y ai vu une bande de jeunes", "C’est le genre de balade qu’on fait en mode cool"])
            result["digueEquipment"] = all(text in source for text in ["24 mètres sur 12", "square du 18 Juin", "1983", "plus de 180 espèces", "1990", "128 promenade de la Digue"])
            result["digueParking"] = "45 places" in source and "18 emplacements" in source and "mentionne 22" in source and "capacité est donc à confirmer" in source
            result["digueAccessibilityQualified"] = "varier selon le tronçon" in source and "garantie d’accessibilité" in source
            result["digueFAQ"] = source.count('class="qa"') == 7 and "Questions / réponses" in source
            result["digueExistingFAQPreserved"] = "Que peut-on voir près de la promenade de la Digue à Nyons ?" in source
            result["digueFAQSchema"] = '"@type":"FAQPage"' in source
            result["digueReaderQuestions"] = all(text in source for text in ["Vous vous promenez souvent sur la Digue ?", "Et quelle autre petite balade facile"])
            result["digueSources"] = "Sources et liens utiles" in source and "dossier-de-plu-approuve" in source and "equipements-sportifs" in source
            result["digueNoInventedPublicationDate"] = "datePublished" not in source and '"dateModified":"2026-10-08"' in source
            headings = re.findall(r"<h2[^>]*>(.*?)</h2>", source, re.S)
            result["digueNoDuplicateHeadings"] = len(headings) == len(set(headings))
        if url.endswith("/que-faire-nyons/") or url.endswith("/toutes-les-pages/"):
            result["digueCardUpdated"] = "Promenade de la Digue à Nyons : balade facile en famille au bord de l’Eygues" in source
        if "/sante-nyons/teleassistance-nyons/" in url:
            result["teleTables"] = source.count('<table class="tele-table">') == 4
            result["teleResponsive"] = "overflow-x:auto" in source and "max-width:100%" in source
            result["telePhotos"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/teleassistance-nyons/[^"]+)"', source)
            result["teleDimensions"] = all(value in source for value in ['width="240" height="267"', 'width="272" height="278"', 'width="188" height="201"'])
            result["teleTariffs"] = "8,27 € par mois" in source and "11,45 € par mois" in source and "8 octobre 2026" in source
            result["teleDetectorQualified"] = "Aucun dispositif automatique ne garantit la détection de toutes les chutes." in source
            result["teleAPAQualified"] = "prise en charge n’est pas automatique" in source
            result["teleTaxQualified"] = all(text in source for text in ["50 %", "après déduction des aides", "La seule vente ou location", "attestation fiscale"])
            result["teleCCAS"] = 'href="tel:+33475265027"' in source and 'href="mailto:ccas@nyons.com"' in source and "Sur rendez-vous" in source
            result["teleMDA"] = 'href="tel:+33475797009"' in source and "fermé le jeudi après-midi" in source
            result["teleFAQ"] = source.count('class="qa"') == 7 and "Questions / réponses" in source
            result["teleFAQSchema"] = '"@type":"FAQPage"' in source
            result["teleReaders"] = all(text in source for text in ["Avez-vous déjà installé une téléassistance", "simple bouton d’alerte", "Et quelle autre aide pour rester à domicile"])
            result["teleSources"] = "Sources et liens utiles" in source and "service-public.gouv.fr/particuliers/vosdroits/F12" in source
            result["teleDate"] = '"datePublished":"2026-10-08"' in source
            result["teleDeviceImagesQualified"] = "Ce modèle n’est pas présenté comme le matériel fourni par Drôme Téléassistance." in source
            headings = re.findall(r"<h2[^>]*>(.*?)</h2>", source, re.S)
            result["teleNoDuplicateHeadings"] = len(headings) == len(set(headings))
            result["teleHeaderWeather"] = 'data-weather-nav="direct"' in source and '/meteo-nyons/' in source
        if url in ["https://www.vivreanyons.fr/", "https://www.vivreanyons.fr/vivreanyons-test/", "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/"]:
            result["latestTeleArticle"] = 'data-latest-article="/sante-nyons/teleassistance-nyons/"' in source
            result["teleHomepagePhoto"] = '/assets/photos/teleassistance-nyons/bouton-bracelet.png' in source
            result["teleClickableTitle"] = bool(re.search(r'<h2 id="new-article-title"><a[^>]+href="[^"]*/sante-nyons/teleassistance-nyons/"', source))
            result["compactWeatherPreserved"] = 'data-weather-compact="true"' in source and 'data-weather-nav="direct"' in source
        if url.endswith("/sante-nyons/") or url.endswith("/infos-pratiques-nyons/") or url.endswith("/toutes-les-pages/"):
            result["teleIndexLinked"] = '/sante-nyons/teleassistance-nyons/' in source
        if "/infos-pratiques-nyons/dechetterie-nyons/" in url:
            result["dechetPhone"] = 'href="tel:+33772325527"' in source
            result["dechetHours"] = all(text in source for text in ["9 h à 12 h", "14 h à 17 h", "15 septembre 2026"])
            result["dechetAccess"] = "justificatif de domicile" in source and "1 m³ par jour" in source and "2 m³ par jour" in source
            result["dechetPhotos"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/dechetterie-nyons/[^"]+)"', source)
            result["dechetDimensions"] = 'width="270" height="171"' in source and 'width="235" height="161"' in source
            result["dechetFAQ"] = source.count('<div class="qa">') == 5 and 'Questions / réponses' in source
            result["dechetFAQSchema"] = '"@type":"FAQPage"' in source
            result["dechetReaderQuestions"] = all(text in source for text in ["Utilisez-vous régulièrement la déchetterie de Nyons ?", "Y a-t-il un type de déchet", "Et quels autres services pratiques"])
            result["dechetSources"] = 'Sources et liens utiles' in source and 'https://www.cc-bdp.fr/les-services/gestion-des-dechets/decheteries/' in source
            result["dechetPublicationDate"] = '"datePublished":"2026-10-08"' in source
            result["dechetDuplicateHeadings"] = source.count("Quels sont les horaires de la déchetterie de Nyons ?") == 1 and source.count("Peut-on apporter des pneus à la déchetterie de Nyons ?") == 1
            result["headings"] = re.findall(r"<h1[^>]*>(.*?)</h1>", source, re.S)
        if url in ["https://www.vivreanyons.fr/", "https://www.vivreanyons.fr/vivreanyons-test/", "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/"]:
            result["latestDechetArticle"] = 'data-latest-article="/infos-pratiques-nyons/dechetterie-nyons/"' in source
            result["dechetHomepagePhoto"] = '/assets/photos/dechetterie-nyons/panneau-dechetterie.png' in source
            result["dechetClickableTitle"] = bool(re.search(r'<h2 id="new-article-title"><a[^>]+href="[^"]*/infos-pratiques-nyons/dechetterie-nyons/"', source))
        if url.endswith("/infos-pratiques-nyons/") or url.endswith("/toutes-les-pages/"):
            result["dechetIndexLinked"] = '/infos-pratiques-nyons/dechetterie-nyons/' in source
        if "/infos-pratiques-nyons/apa-nyons/" in url:
            result["apaEligibility"] = all(text in source for text in ["60 ans", "GIR 1 à GIR 4", "résider en France de façon stable et régulière"])
            result["apaMeansClarified"] = "Il n’existe pas de plafond de ressources" in source and "participation financière" in source
            result["apaCCAS"] = 'href="tel:+33475265027"' in source and "ccas@nyons.com" in source and "sur rendez-vous" in source
            result["apaDepartment"] = 'href="tel:+33475797009"' in source and "dromesolidarites@ladrome.fr" in source
            result["apaOfficialForm"] = "https://www.ladrome.fr/wp-content/uploads/2022/06/formulaire-aideautonomiepa-interactif-v4.pdf" in source
            result["apaPhoto"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/apa-nyons/[^"]+)"', source)
            result["apaPhotoDimensions"] = 'width="260" height="242"' in source
            result["apaFAQ"] = source.count('<div class="qa">') == 5 and "Questions / réponses" in source
            result["apaFAQSchema"] = '"@type":"FAQPage"' in source
            result["apaReaderQuestions"] = all(text in source for text in ["Avez-vous déjà constitué un dossier APA", "Les démarches vous ont-elles paru simples ?", "Et quel autre sujet aimeriez-vous"])
            result["apaSources"] = "Sources et liens utiles" in source and "service-public.gouv.fr/particuliers/vosdroits/F10009" in source
            result["apaDate"] = '"datePublished":"2026-10-08"' in source
            result["apaNoDuplicateHeadings"] = re.findall(r"<h2[^>]*>(.*?)</h2>", source).count("Aide à domicile : que peut financer l’APA ?") == 1 and re.findall(r"<h2[^>]*>(.*?)</h2>", source).count("À retenir") == 1
        if url in ["https://www.vivreanyons.fr/", "https://www.vivreanyons.fr/vivreanyons-test/", "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/"]:
            result["latestAPAArticle"] = 'data-latest-article="/infos-pratiques-nyons/apa-nyons/"' in source
            result["apaHomepagePhoto"] = '/assets/photos/apa-nyons/apa-a-domicile.png' in source
            result["apaClickableTitle"] = bool(re.search(r'<h2 id="new-article-title"><a[^>]+href="[^"]*/infos-pratiques-nyons/apa-nyons/"', source))
        if url.endswith("/infos-pratiques-nyons/") or url.endswith("/toutes-les-pages/") or url.endswith("/sante-nyons/"):
            result["apaIndexLinked"] = '/infos-pratiques-nyons/apa-nyons/' in source
        if "/infos-pratiques-nyons/dechetterie-nyons/" in url:
            result["dechetTables"] = source.count('<table class="dechet-table">') == 4
            result["dechetMobileTables"] = ".dechet-table-wrap" in source and "overflow-x:auto" in source
        if "/infos-pratiques-nyons/apa-nyons/" in url:
            result["apaTables"] = source.count('<table class="apa-table">') == 4
            result["apaMobileTables"] = ".apa-table-wrap" in source and "overflow-x:auto" in source
        if "/sante-nyons/kinesitherapeute-nyons/" in url:
            result["kineTables"] = source.count('<table class="kine-table">') == 4
            result["kineMobileTables"] = ".kine-table-wrap" in source and "overflow-x:auto" in source
            result["kinePhotos"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/kinesitherapeute-nyons/[^"]+)"', source)
            result["kineDimensions"] = all(size in source for size in ['width="226" height="222"', 'width="206" height="180"', 'width="205" height="185"'])
            result["kineCaptions"] = source.count("Photo d’illustration.") == 3
            result["kineContacts"] = 'href="tel:+33767297759"' in source and 'href="tel:+33681538648"' in source
            result["kineDomicileQualified"] = "médicalement justifiés" in source or "médicalement justifié" in source
            result["kineAccessDirect"] = "huit séances" in source and "certaines structures" in source
            result["kineReimbursement"] = "60 % de la base de remboursement" in source and "1 € par acte paramédical" in source
            result["kineFranchiseQualified"] = "Elle n’est pas remboursée par la complémentaire santé." in source and "sauf exonération" in source
            result["kineEmergency"] = 'href="tel:15"' in source and 'href="tel:112"' in source
            result["kineFAQ"] = source.count('<div class="qa">') == 6 and "Questions / réponses" in source
            result["kineFAQSchema"] = '"@type":"FAQPage"' in source
            result["kineReaders"] = all(text in source for text in ["Avez-vous déjà eu des difficultés", "Avez-vous déjà bénéficié", "Et quel autre sujet pratique"])
            result["kineSources"] = "Sources et liens utiles" in source and "legifrance.gouv.fr" in source and "ameli.fr" in source
            result["kineDate"] = '"datePublished":"2026-10-08"' in source
            result["kineNoPastedDuplicates"] = "Vous pouvez Vous pouvez" not in source and source.count("Kiné à domicile pour une personne âgée") == 1
            result["headings"] = re.findall(r"<h1[^>]*>(.*?)</h1>", source, re.S)
        if url in ["https://www.vivreanyons.fr/", "https://www.vivreanyons.fr/vivreanyons-test/", "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/"]:
            result["latestKineArticle"] = 'data-latest-article="/sante-nyons/kinesitherapeute-nyons/"' in source
            result["kineHomepagePhoto"] = "/assets/photos/kinesitherapeute-nyons/soins-du-dos.png" in source
            result["kineClickableTitle"] = bool(re.search(r'<h2 id="new-article-title"><a[^>]+href="[^"]*/sante-nyons/kinesitherapeute-nyons/"', source))
        if url.endswith("/infos-pratiques-nyons/") or url.endswith("/toutes-les-pages/") or url.endswith("/sante-nyons/"):
            result["kineIndexLinked"] = "/sante-nyons/kinesitherapeute-nyons/" in source
        if "/infos-pratiques-nyons/marche-vaison-la-romaine/" in url:
            result["vaisonTables"] = source.count('<table class="vaison-table">') == 3
            result["vaisonMobileTables"] = ".vaison-table-wrap" in source and "overflow-x:auto" in source
            result["vaisonPhotos"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/marche-vaison-la-romaine/[^"]+)"', source)
            result["vaisonDimensions"] = all(size in source for size in ['width="222" height="243"', 'width="298" height="285"', 'width="220" height="253"', 'width="251" height="238"', 'width="260" height="288"'])
            result["vaisonHours"] = "8 h 30 à 13 h" in source and "7 h 30" in source
            result["vaisonProducers"] = all(text in source for text in ["le mardi et le samedi de 8 h à 12 h", "Général-de-Gaulle", "contre-allée Burrus"])
            result["vaisonHistory"] = all(text in source for text in ["1483", "1532", "450 exposants"])
            result["vaisonParkingQualified"] = all(text in source for text in ["septembre 2024", "mai 2025", "zone bleue", "Pont Romain", "pas une promesse de places libres"])
            result["vaisonContact"] = 'href="tel:+33490365000"' in source
            result["vaisonFAQ"] = source.count('<div class="qa">') == 6 and "Questions / réponses" in source
            result["vaisonFAQSchema"] = '"@type":"FAQPage"' in source
            result["vaisonReaders"] = all(text in source for text in ["Vous connaissez le marché de Vaison-la-Romaine ?", "Vous le préférez", "trouver une place le mardi matin"])
            result["vaisonSources"] = "Sources et liens utiles" in source and "provenceguide.com" in source and "vaison-la-romaine.com" in source
            result["vaisonDate"] = '"datePublished":"2026-10-08"' in source
            result["vaisonReviewProvenanceRemoved"] = all(text not in source for text in ["avis que tu m", "avis transmis", "MÉMOIRE LOCALE"])
            result["vaisonNoDuplicateHeadings"] = re.findall(r"<h2[^>]*>(.*?)</h2>", source).count("Où se garer pour le marché ?") == 1 and re.findall(r"<h2[^>]*>(.*?)</h2>", source).count("Un marché touristique ? Oui… mais pas seulement") == 1
            result["headings"] = re.findall(r"<h1[^>]*>(.*?)</h1>", source, re.S)
        if url in ["https://www.vivreanyons.fr/", "https://www.vivreanyons.fr/vivreanyons-test/", "https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/"]:
            result["latestVaisonArticle"] = 'data-latest-article="/infos-pratiques-nyons/marche-vaison-la-romaine/"' in source
            result["vaisonHomepagePhoto"] = "/assets/photos/marche-vaison-la-romaine/etal-marche.png" in source
            result["vaisonClickableTitle"] = bool(re.search(r'<h2 id="new-article-title"><a[^>]+href="[^"]*/infos-pratiques-nyons/marche-vaison-la-romaine/"', source))
        if url.endswith("/infos-pratiques-nyons/") or url.endswith("/toutes-les-pages/") or url.endswith("/a-faire-autour-de-Nyons/"):
            result["vaisonIndexLinked"] = "/infos-pratiques-nyons/marche-vaison-la-romaine/" in source
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
            result["latestPortageArticle"] = 'data-latest-article="/infos-pratiques-nyons/portage-repas-nyons/"' in source
            result["portageHomepagePhoto"] = "/assets/photos/portage-repas-nyons/repas-servi-a-domicile.png" in source
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
            result["healthItems26"] = '"numberOfItems":26' in source
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
            result["portageFeatured"] = bool(re.search(r'data-latest-article="[^"]*infos-pratiques-nyons/portage-repas-nyons/"', source))
            result["portageHomepagePhoto"] = "assets/photos/portage-repas-nyons/repas-servi-a-domicile.png" in source
        if url in ["https://www.vivreanyons.fr/sante-nyons/","https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/","https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/"]:
            result["radiologyLinked"] = bool(re.search(r'href="[^"]*sante-nyons/radiologie-nyons/"', source))
            result["healthItems26"] = '"numberOfItems":26' in source
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
            result["contactCards"] = len(re.findall(r'class="msp-contact"', source))
            result["contactPhoneLine"] = "white-space:nowrap" in source and 'class="msp-contact-phone"' in source
            result["contactsTableRemoved"] = "msp-table-wrap" not in source and "<table" not in source
            result["faqVisible"] = 'id="faq-maison-sante"' in source and len(re.findall(r'<div class="qa">', source)) == 5
            result["faqSchema"] = '"@type":"FAQPage"' in source
            result["sourcesVisible"] = 'id="sources-maison-sante"' in source and "Sources et liens utiles" in source
            result["localDiscussionSource"] = "https://www.facebook.com/groups/nyonsaujourdhui/posts/1223967436583187/" in source
            result["sevenSources"] = source.count('target="_blank" rel="noopener noreferrer"') >= 7
            result["readerQuestionsPreserved"] = "Et vous, comment cela se passe-t-il ?" in source
            result["photoCaptions"] = len(re.findall(r"<figcaption>", source))
            result["photos"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/maison-de-sante-nyons/[^"]+)"', source)
            result["oldIllustrationRemoved"] = "assets/photos/668de5d6a91a56f4b265.webp" not in source
            result["headings"] = re.findall(r"<h1[^>]*>(.*?)</h1>", source, re.S)
            result["editorialHeadings"] = len(re.findall(r"<h2", source))
            result["publishDate"] = '"datePublished":"2026-10-07"' in source
        if "/infos-pratiques-nyons/portage-repas-nyons/" in url:
            result["ccasContact"] = 'href="tel:+33475265027"' in source and "ccas@nyons.com" in source
            result["deliveryHours"] = "7 h 30 et 11 h 30" in source and "du lundi au samedi" in source
            result["publishedPricesQualified"] = all(text in source for text in ["8,50 € le repas", "10 € le repas", "8,80 € ou 10,30 €", "Confirmez le prix actuellement applicable"])
            result["thresholdQualified"] = "revenus pris en compte et le seuil applicable" in source
            result["delay48Hours"] = "48 heures à l’avance" in source
            result["apaConditional"] = "Cette aide n’est pas automatique" in source and "GIR 1 à 4" in source
            result["statistics2025"] = all(text in source for text in ["2025", "15 506", "66 bénéficiaires"])
            result["sundayArrangement"] = "repas doublé le samedi pour le dimanche" in source
            result["photos"] = re.findall(r'<img[^>]+src="([^"]*assets/photos/portage-repas-nyons/[^"]+)"', source)
            result["photoCaptions"] = len(re.findall(r"<figcaption>", source))
            result["faqVisible"] = 'id="questions"' in source and source.count('<div class="qa">') == 7
            result["faqSchema"] = '"@type":"FAQPage"' in source
            result["sourcesVisible"] = "Sources et liens utiles" in source and 'class="meal-sources"' in source
            result["sourcesCount"] = len(re.findall(r"<li>", re.search(r'<section class="meal-sources".*?</section>', source, re.S).group(0))) if 'class="meal-sources"' in source else 0
            result["readerQuestions"] = "Et vous, connaissiez-vous ce service ?" in source
            result["publishDate"] = '"datePublished":"2026-10-07"' in source
            result["headings"] = re.findall(r"<h1[^>]*>(.*?)</h1>", source, re.S)
        if url in ["https://www.vivreanyons.fr/sante-nyons/","https://www.vivreanyons.fr/vivreanyons-test/sante-nyons/","https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/sante-nyons/"]:
            result["portageLinked"] = "data-portage-repas-card" in source and "portage-repas-nyons/" in source
        if url in ["https://www.vivreanyons.fr/infos-pratiques-nyons/","https://www.vivreanyons.fr/toutes-les-pages/","https://www.vivreanyons.fr/vivreanyons-test/infos-pratiques-nyons/","https://www.vivreanyons.fr/vivreanyons-test/toutes-les-pages/","https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/","https://www.vivreanyons.fr/banniere-nyons/vivreanyons-test/toutes-les-pages/"]:
            result["portageLinked"] = "data-portage-repas-card" in source and "portage-repas-nyons/" in source
        if url.endswith("/que-faire-nyons/les-vieux-moulins/"):
            result["infoAdded"] = 'data-vieux-moulins-infos="2026-10-07"' in source
            result["address"] = "4 promenade de la Digue, 26110 Nyons" in source
            result["currentContact"] = 'href="tel:+33673871145"' in source and "lesvieuxmoulins.nyons@gmail.com" in source
            result["visitDuration"] = "30 à 45 minutes" in source
            result["childrenTariff2026"] = "5 € à partir de 10 ans" in source and "gratuité pour les enfants de moins de 10 ans" in source
            result["guidedBooking"] = "visites guidées uniquement sur rendez-vous" in source
            result["historicDates"] = "moulin de 1780" in source and "jusqu’en 1952" in source
            result["originalPhotos"] = all(photo in source for photo in ["fiche-2038b7f67c32d62b528b.webp", "fiche-21a4b36d1f94e4afe471.webp"])
            result["photoDimensions"] = 'width="1280" height="883"' in source and 'width="853" height="1280"' in source
            result["faqCount"] = len(re.findall(r'<div class="qa">', source))
            result["faqSchema"] = '"@type":"FAQPage"' in source
            result["noInventedPublicationDate"] = "datePublished" not in source
            result["readerQuestions"] = "Avez-vous déjà visité Les Vieux Moulins ou êtes-vous passé devant sans jamais descendre ?" in source
            article = re.search(r'<article class="feature-story">.*?</article>', source, re.S).group(0)
            article = re.sub(r'<section class="mills-practical".*?</section>', "", article, flags=re.S)
            original_text = re.sub(r"\s+", " ", re.sub(r"<[^>]*>", "", article)).strip()
            text_hash = 2166136261
            for char in original_text:
                text_hash = ((text_hash ^ ord(char)) * 16777619) & 0xffffffff
            result["originalTextPreserved"] = format(text_hash, "08x") == "fa1d138f"
        if page.refresh:
            match = re.search(r"^\s*0\s*;\s*url\s*=\s*(.+?)\s*$", page.refresh, re.I)
            if match:
                result["instantRefreshDestination"] = urljoin(result["final"], match.group(1).strip("\"'"))
    except HTTPError as error:
        result.update({"status": error.code, "final": error.geturl(), "chain": chain, "error": str(error)})
    except Exception as error:
        result.update({"status": None, "chain": chain, "error": str(error)})
    return result

for attempt in range(12):
    ready_article = check("https://www.vivreanyons.fr/que-faire-nyons/promenade-de-la-digue-nyons/")
    ready_home = check("https://www.vivreanyons.fr/")
    if ready_article.get("digueUpdated") and ready_article.get("digueFAQ") and ready_home.get("latestTeleArticle"):
        break
    print("Waiting for the updated Digue article and preserved homepage:", attempt + 1, flush=True)
    time.sleep(10)

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(check, URLS))
print("PUBLIC_URL_AUDIT_BEGIN")
print(json.dumps({"checkedDate": "2026-10-08", "readOnly": True, "results": results}, ensure_ascii=False, indent=2))
print("PUBLIC_URL_AUDIT_END")

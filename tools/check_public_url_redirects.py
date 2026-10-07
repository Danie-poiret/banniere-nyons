"""Read-only checks of the public URLs reported by Search Console."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError

URLS = [
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
            source = response.read(2000000).decode("utf-8", errors="replace")
        page = Page()
        page.feed(source)
        result.update({"canonicals": page.canonicals, "robots": page.robots, "metaRefresh": page.refresh})
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

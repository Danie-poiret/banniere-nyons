"""Check repository signals and optionally live HTTP responses for nine URLs."""
import argparse
import concurrent.futures
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, HTTPRedirectHandler, build_opener
import xml.etree.ElementTree as ET
from indexing_targets import SITE, PREFIXES, SLUGS, canonical_link

ROOT = Path(__file__).resolve().parents[1]
class Parse(HTMLParser):
    def __init__(self, source):
        super().__init__(); self.canonicals=[]; self.robots=[]; self.feed(source)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='link' and a.get('rel')=='canonical': self.canonicals.append(a.get('href'))
        if tag=='meta' and a.get('name','').lower()=='robots': self.robots.append(a.get('content'))

def check_repository():
    errors=[]; urls=[SITE+s for s in SLUGS]
    for prefix in PREFIXES:
        for slug in SLUGS:
            file=ROOT/(prefix+slug+'index.html'); p=Parse(file.read_text(encoding='utf-8'))
            if p.canonicals != [SITE+slug]: errors.append(f'{file.relative_to(ROOT)}: canonical {p.canonicals}')
            expected='noindex,nofollow' if prefix else 'index,follow'
            if p.robots != [expected]: errors.append(f'{file.relative_to(ROOT)}: robots {p.robots}')
    locations=[n.text for n in ET.parse(ROOT/'sitemap.xml').getroot().findall('{*}url/{*}loc')]
    for url in urls:
        if locations.count(url)!=1: errors.append(f'Sitemap must contain canonical once: {url}')
    for url in locations:
        if canonical_link(url,'index.html')!=url: errors.append(f'Noncanonical sitemap entry: {url}')
    needles=tuple(s.rstrip('/').rsplit('/',1)[-1].lower() for s in SLUGS)
    checked=0
    for file in ROOT.rglob('*.html'):
        if '.git' in file.parts: continue
        source=file.read_text(encoding='utf-8')
        if not any(n in source.lower() for n in needles): continue
        relative=file.relative_to(ROOT).as_posix()
        for raw in re.findall(r'''\bhref\s*=\s*["']([^"']+)["']''',source,re.I):
            raw=html.unescape(raw); checked+=1
            if canonical_link(raw,relative)!=raw: errors.append(f'{relative}: inconsistent link {raw}')
    print(f'Repository: 27 canonical/robots pairs, 9 sitemap targets and {checked} href attributes checked.')
    return errors

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

def get(url):
    request=Request(url,headers={'User-Agent':'VivreAnyons-SEO-verification/1.0','Cache-Control':'no-cache'})
    try: response=build_opener(NoRedirect).open(request,timeout=30)
    except HTTPError as e: response=e
    with response: return response.status, response.headers.get('Location'), response.read(2000000).decode('utf-8',errors='replace')

def check_live_one(item):
    url, slug, prefix, bare=item
    try:
        status, location, source=get(url)
        if bare: ok=status==301 and location==SITE+slug
        else:
            p=Parse(source); expected='noindex,nofollow' if prefix else 'index,follow'
            ok=status==200 and p.canonicals==[SITE+slug] and p.robots==[expected]
        return {'url':url,'status':status,'location':location,'ok':ok}
    except Exception as e: return {'url':url,'ok':False,'error':str(e)}

def check_live():
    items=[(SITE+prefix+slug,slug,prefix,False) for prefix in PREFIXES for slug in SLUGS]
    items += [(SITE+slug.rstrip('/'),slug,'',True) for slug in SLUGS]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: results=list(pool.map(check_live_one,items))
    print('INDEXING_LIVE_AUDIT_BEGIN'); print(json.dumps(results,ensure_ascii=False,indent=2)); print('INDEXING_LIVE_AUDIT_END')
    return [r for r in results if not r['ok']]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--live',action='store_true'); args=parser.parse_args()
    errors=check_repository()
    if args.live: errors += check_live()
    if errors:
        print(json.dumps(errors,ensure_ascii=False,indent=2)); raise SystemExit(1)
    print('All indexing checks passed.')

if __name__=='__main__': main()

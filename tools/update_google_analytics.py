"""Install the shared consent-controlled Google tag and direct lodging menu link."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
VERSION='google-analytics-20261008-v1'
PATTERN=re.compile(r'(<script\b[^>]*\bsrc=["\'])([^"\']*assets/agenda\.js)(?:\?[^"\']*)?(["\'][^>]*>)',re.I)
PREFIXES=('', 'vivreanyons-test/', 'banniere-nyons/vivreanyons-test/')
def prefix_for(path):
    text=path.relative_to(ROOT).as_posix()
    for prefix in sorted(PREFIXES,key=len,reverse=True):
        if prefix and text.startswith(prefix):
            return prefix
    return ''
def main():
    pages=sorted(ROOT.rglob('*.html'))
    plans=[]
    covered=0
    raw_tags=[]
    for path in pages:
        if '.git' in path.parts: continue
        source=path.read_text(encoding='utf-8')
        if re.search(r'googletagmanager\.com/(?:gtag/js|gtm\.js)|\bgtag\s*\(|google-analytics\.com/analytics\.js',source,re.I):
            raw_tags.append(str(path.relative_to(ROOT)))
        if re.search(r'<meta\b[^>]*http-equiv=["\']refresh',source,re.I): continue
        updated=PATTERN.sub(lambda m:m.group(1)+m.group(2)+'?v='+VERSION+m.group(3),source)
        if '<header>' not in source or 'class="navlinks"' not in source:
            if updated!=source:plans.append((path,updated))
            continue
        prefix=prefix_for(path)
        if not PATTERN.search(updated):
            assert '</body>' in updated, path
            updated=updated.replace('</body>','<script src="/'+prefix+'assets/agenda.js?v='+VERSION+'"></script></body>',1)
        covered+=1
        # The direct item and the existing rubrique link serve separate menu levels.
        updated=re.sub(r'<a\b(?=[^>]*\bdata-nyons-shortcut=["\']hebergement["\'])[^>]*>.*?</a>', '', updated, flags=re.S)
        navigation=re.search(r'<header>[\s\S]*?</header>',updated)
        assert navigation, path
        nav=navigation.group(0)
        item='<a data-nyons-shortcut="hebergement" href="/'+prefix+'ou-dormir-a-nyons/">Où dormir à Nyons ?</a>'
        if '<details class="rubriques">' in nav:
            nav=nav.replace('<details class="rubriques">',item+'<details class="rubriques">',1)
        else:
            nav=nav.replace('<div class="navlinks">','<div class="navlinks">'+item,1)
        updated=updated[:navigation.start()]+nav+updated[navigation.end():]
        if updated!=source:plans.append((path,updated))
    assert not raw_tags, 'Review existing direct Google tags before adding the shared tag: '+', '.join(raw_tags)
    for prefix in PREFIXES:
        js=(ROOT/prefix/'assets/agenda.js').read_text(encoding='utf-8')
        assert js.count("window.gtag('config',ANALYTICS_ID,")==1
        assert "const ANALYTICS_ID='G-X0T2SGWSWX'" in js
        assert 'name="analytics"' in js
    for path,source in plans:path.write_text(source,encoding='utf-8')
    print(f'Google Analytics: {covered} shared-script pages; {len(plans)} updated files; zero direct duplicate Google tags.')
if __name__=='__main__': main()

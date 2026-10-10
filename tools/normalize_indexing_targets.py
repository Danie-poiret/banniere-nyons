"""Keep canonical links consistent without editing text, photos or old URLs."""
import html
import json
import re
from pathlib import Path
from indexing_targets import SITE, SLUGS, canonical_link

ROOT = Path(__file__).resolve().parents[1]
ATTR = re.compile(r'''(?P<lead>\bhref\s*=\s*["'])(?P<url>[^"']+)(?P<end>["'])''', re.I)

def main():
    changed = []; count = 0
    needles = tuple(s.rstrip('/').rsplit('/', 1)[-1].lower() for s in SLUGS)
    for file in ROOT.rglob('*.html'):
        if '.git' in file.parts: continue
        source = file.read_bytes().decode('utf-8')
        if not any(n in source.lower() for n in needles): continue
        relative = file.relative_to(ROOT).as_posix()
        def change(match):
            nonlocal count
            raw = html.unescape(match['url'])
            replacement = canonical_link(raw, relative)
            if replacement == raw: return match.group()
            count += 1
            return match['lead'] + html.escape(replacement, quote=True) + match['end']
        updated = ATTR.sub(change, source)
        if updated != source:
            file.write_bytes(updated.encode('utf-8')); changed.append(relative)
    if changed:
        audit = {'date':'2026-10-10', 'canonicalURLs':[SITE+s for s in SLUGS], 'changedFiles':changed, 'urlAttributesUpdated':count, 'scope':'href attributes only; text, photographs, publication dates and URL paths preserved'}
        (ROOT/'tools/editorial-checks/indexing-duplicates-2026-10-10.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Canonical URL alignment: {count} attributes updated in {len(changed)} files.')

if __name__ == '__main__': main()

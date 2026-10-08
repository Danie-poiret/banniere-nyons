"""Add one direct weather link to the common menu, including mirrored pages."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
changed = checked = 0
for file in root.rglob("index.html"):
    relative = file.relative_to(root).as_posix()
    if relative.startswith((".git/", "tools/", ".github/")):
        continue
    source = file.read_text(encoding="utf-8")
    match = re.search(r'(<div class="navlinks">)(.*?)(</nav>)', source, re.S)
    if not match:
        continue
    checked += 1
    prefix = next((p for p in ("banniere-nyons/vivreanyons-test/", "vivreanyons-test/") if relative.startswith(p)), "")
    href = "/" + prefix + "meteo-nyons/"
    content = match.group(2)
    direct, separator, rest = content.partition("<details")
    # Replace an existing direct weather link instead of duplicating it.
    direct = re.sub(r'<a\b[^>]*href="(?:[^"]*/meteo-nyons/|#meteo-nyons)"[^>]*>.*?</a>', "", direct, flags=re.S)
    current = ' aria-current="page"' if relative == prefix + "meteo-nyons/index.html" else ""
    link = '<a data-weather-nav="direct" href="' + href + '"' + current + '>Météo</a>'
    health = re.search(r'<a\b[^>]*data-(?:nyons-today-nav|health-nav)="direct"', direct)
    if health:
        direct = direct[:health.start()] + link + direct[health.start():]
    elif separator:
        direct += link
    else:
        direct = direct.replace("</div>", link + "</div>", 1)
    updated_menu = match.group(1) + direct + separator + rest + match.group(3)
    updated = source[:match.start()] + updated_menu + source[match.end():]
    assert updated_menu.count('data-weather-nav="direct"') == 1
    if updated != source:
        file.write_text(updated, encoding="utf-8")
        changed += 1
print("Menu météo :", checked, "pages vérifiées ;", changed, "pages mises à jour.")

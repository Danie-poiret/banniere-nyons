"""Shared official data for Nyons. No visitor requests and no AI calls.
Each source fails independently; never carry an old status forward as current.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse
import json, math, re

ROOT = Path(__file__).resolve().parents[1]
PARIS = ZoneInfo("Europe/Paris")
AIR = "https://www.atmo-auvergnerhonealpes.fr/air-commune/Ville/26220/indice-atmo"
RIVER = "https://www.vigicrues.gouv.fr/services/observations.json/?CdStationHydro=V533401002&GrdSerie=H&FormatDate=iso"
FIRE = "https://www.risque-prevention-incendie.fr/drome"
WATER = "https://api.vigieau.beta.gouv.fr/api/zones?commune=26220&profil=particulier&zoneType=SUP"
now = datetime.now(timezone.utc)
today = now.astimezone(PARIS).date()
end_day = datetime.combine(today + timedelta(days=1), datetime.min.time(), PARIS)

def iso(value):
    return value.isoformat(timespec="seconds")
def parsed(value):
    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("Date sans fuseau")
    return value
def request(url):
    with urlopen(Request(url, headers={"User-Agent": "VivreAnyons/1.0 (contact@vivreanyons.fr)", "Accept": "application/json,text/html", "Cache-Control": "no-cache"}), timeout=18) as response:
        body = response.read(3_000_001)
        if len(body) > 3_000_000:
            raise ValueError("Réponse trop volumineuse")
        return body.decode("utf-8-sig")
def available(label, detail, expires, **extra):
    return {"status":"available", "label":label, "detail":detail,
            "checkedAt":iso(now), "validUntil":iso(min(expires, now + timedelta(hours=12))), **extra}
class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bits = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip-1)
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.bits.append(data.strip())

def parse_air(body):
    parser = Text(); parser.feed(body)
    text = "\n".join(parser.bits)
    labels = "Extrêmement mauvais|Très mauvais|Mauvais|Dégradé|Moyen|Bon"
    match = re.search(r"Qualité de l.air à Nyons\n(.*?)\n(" + labels + r")\nSur les 12 derniers mois", text, re.S)
    if not match:
        raise ValueError("Indice communal non identifiable")
    months = ("janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre")
    dated = re.search(r"\b(\d{1,2})(?:er)?\s+([a-zéû]+)", match[1].lower())
    if not dated or int(dated[1]) != today.day or dated[2] != months[today.month-1]:
        raise ValueError("Bulletin ATMO ne concerne pas aujourd'hui")
    updated = re.search(r"Données mises à jour le (\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}:\d{2})", text)
    if not updated:
        raise ValueError("Date ATMO absente")
    observed = datetime.strptime(updated[1]+" "+updated[2], "%d/%m/%Y %H:%M").replace(tzinfo=PARIS)
    if not timedelta(0) <= now-observed <= timedelta(hours=48):
        raise ValueError("Publication ATMO trop ancienne ou future")
    return available("Indice ATMO : "+match[2], "Indice du jour · publié le "+observed.strftime("%d/%m à %H:%M"), end_day,
                     date=today.isoformat(), observedAt=iso(observed), source=AIR)
def air():
    return parse_air(request(AIR))

def parse_river(body):
    series = json.loads(body)["Serie"]
    if series.get("CdStationHydro") != "V533401002" or series.get("GrdSerie") != "H":
        raise ValueError("Station ou grandeur incorrecte")
    points = [p for p in series["ObssHydro"] if isinstance(p.get("ResObsHydro"), (int,float)) and not isinstance(p["ResObsHydro"],bool) and math.isfinite(p["ResObsHydro"])]
    latest = max(points, key=lambda p:parsed(p["DtObsHydro"]))
    observed = parsed(latest["DtObsHydro"])
    if not timedelta(0) <= now-observed <= timedelta(hours=6):
        raise ValueError("Mesure Vigicrues trop ancienne ou future")
    height = latest["ResObsHydro"]
    if not -10 <= height <= 30:
        raise ValueError("Hauteur incohérente")
    label = f"Hauteur : {height:.2f} m".replace(".", ",")
    return available(label, "Pont de l’Europe · relevé le "+observed.astimezone(PARIS).strftime("%d/%m à %H:%M")+" · hauteur à la station, pas une profondeur de baignade", observed+timedelta(hours=6),
                     observedAt=iso(observed), heightMetres=height, source=RIVER)
def river():
    return parse_river(request(RIVER))

def parse_fire(body):
    data = json.loads(body)
    values = data.get("massifs", {}).get("267")
    if not isinstance(values,list) or not values or type(values[0]) is not int:
        raise ValueError("Niveau du secteur Nyonsais absent")
    labels = {1:"Niveau vert",2:"Niveau jaune",3:"Niveau rouge",4:"Niveau rouge E"}
    if values[0] not in labels:
        raise ValueError("Niveau incendie non publié")
    return available(labels[values[0]], "Carte du jour · secteur Nyonsais. Vérifier aussi les arrêtés locaux.", end_day, date=today.isoformat(), source=FIRE)
def fire_path(candidates):
    match = next((m for s in candidates if (m:=re.search(r"(?:var |let |const )?url_data\s*=\s*([^;\n]+)",s))), None)
    if not match:
        raise ValueError("Chemin quotidien de la carte non identifiable")
    # String literals and the confirmed department id only; never eval remote JS.
    parts = []
    for token in match[1].strip().split("+"):
        token = token.strip()
        if token == "id":
            parts.append("26")
        elif len(token)>1 and token[0] in ("'", '"') and token[-1] == token[0]:
            parts.append(token[1:-1])
        else:
            raise ValueError("Expression du chemin quotidien non reconnue")
    daily_base = "".join(parts)
    if "import_data" not in daily_base or not daily_base.endswith("/"):
        raise ValueError("Chemin quotidien de la carte incomplet")
    return daily_base

def fire():
    page = request(FIRE)
    if not re.search(r"<tr\s+id=['\"]267['\"][^>]*>\s*<td>.*?</td>\s*<td>Nyonsais</td>", page, re.S):
        raise ValueError("Identifiant du massif non confirmé")
    # Discover the public daily JSON path used by the official map; fail closed
    # if its format changes. Never interpret the map's default level 0 as safe.
    scripts = re.findall(r"<script[^>]+src=['\"]([^'\"]+)", page)
    candidates = [page]
    for src in scripts:
        target = urljoin(FIRE, src)
        if urlparse(target).hostname == "www.risque-prevention-incendie.fr" and ("maps_prev" in src or "massifs_prev" in src):
            candidates.append(request(target))
    daily_base = fire_path(candidates)
    target = urljoin(FIRE, daily_base+today.strftime("%Y%m%d")+".json")
    if urlparse(target).hostname != "www.risque-prevention-incendie.fr":
        raise ValueError("Source incendie inattendue")
    print("FIRE_JSON_SOURCE", target, flush=True)
    result = parse_fire(request(target)); result["dataSource"] = target
    return result

def parse_water(body):
    zones = json.loads(body)
    if not isinstance(zones,list):
        raise ValueError("Réponse VigiEau invalide")
    zones = [z for z in zones if z.get("type")=="SUP" and z.get("code")=="84_26_0009" and z.get("departement")=="26"]
    if len(zones) != 1:
        raise ValueError("Zone E(A)ygues non identifiable sans ambiguïté")
    zone = zones[0]; order = zone.get("arrete") or {}
    levels = {"vigilance":"Vigilance","alerte":"Alerte","alerte_renforcee":"Alerte renforcée","crise":"Crise"}
    if zone.get("niveauGravite") not in levels:
        raise ValueError("Niveau VigiEau absent ; aucune absence de restriction déduite")
    start = parsed(order["dateDebutValidite"]).date()
    end = parsed(order["dateFinValidite"]).date() if order.get("dateFinValidite") else None
    if start > today or (end and end < today):
        raise ValueError("Arrêté hors de sa période de validité")
    expiry = now+timedelta(hours=12)
    if end:
        expiry = min(expiry, datetime.combine(end+timedelta(days=1),datetime.min.time(),PARIS))
    detail = "Bassin de l’Eygues · eaux superficielles"
    if end:
        detail += " · arrêté jusqu’au "+end.strftime("%d/%m/%Y")+", sauf modification"
    return available(levels[zone["niveauGravite"]], detail, expiry, source=WATER, zone=zone["code"], waterType="SUP",
                     orderUrl=order.get("cheminFichier"), orderStart=start.isoformat(), orderEnd=end.isoformat() if end else None)
def water():
    return parse_water(request(WATER))

def main():
    items = {}
    notes = {"air":"Consulte l’indice officiel du jour.", "river":"Consulte les relevés et la vigilance officielle.",
             "fire":"Carte quotidienne non disponible ou non confirmée. Consulter les arrêtés locaux.",
             "water":"Consulte les restrictions officielles selon ton usage de l’eau."}
    for key, adapter in (("air",air),("river",river),("fire",fire),("water",water)):
        try:
            items[key] = adapter()
        except Exception as error:
            print(key, "indisponible :", type(error).__name__, str(error)[:180], flush=True)
            items[key] = {"status":"unavailable", "label":"Donnée indisponible", "detail":notes[key], "checkedAt":iso(now)}
    payload = {"schemaVersion":1, "commune":"26220", "timezone":"Europe/Paris", "collectedAt":iso(now), "items":items}
    destination = ROOT/"assets/nyons-direct.json"
    destination.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":"))+"\n", encoding="utf-8")
    print("NYONS_DIRECT_DATA", json.dumps(payload,ensure_ascii=False), flush=True)
if __name__ == "__main__":
    main()

"""Inspect public provider schemas before writing strict local adapters."""
import json,re
from urllib.request import Request,urlopen
from urllib.parse import urljoin
URLS={
"air":"https://www.atmo-auvergnerhonealpes.fr/air-commune/Ville/26220/indice-atmo",
"widget":"https://api.atmo-aura.fr/pub/create-widget",
"river":"https://www.vigicrues.gouv.fr/services/observations.json/?CdStationHydro=V533401002&GrdSerie=H&FormatDate=iso",
"fire":"https://www.risque-prevention-incendie.fr/drome",
"water":"https://api.vigieau.beta.gouv.fr/api/zones?commune=26220&profil=particulier",
}
for key,url in URLS.items():
    print("\nPROVIDER",key,flush=True)
    try:
        with urlopen(Request(url,headers={"User-Agent":"VivreAnyons/1.0 contact@vivreanyons.fr"}),timeout=20) as r: body=r.read().decode("utf-8")
        if key in ("water","river"):
            data=json.loads(body)
            if key=="water": print(json.dumps(data[:1] if isinstance(data,list) else data,ensure_ascii=False)[:12000])
            else: print(body[:6000])
        else:
            scripts=re.findall(r'<script[^>]+src=["\']([^"\']+)',body)
            print("SCRIPTS",scripts)
            if key=="air":
                index=body.find("Qualité de l"); print(body[max(0,index-500):index+10000])
                print("SETTINGS",body[-10000:])
            else:
                print(body[:8000])
                for src in scripts:
                    if not ("static" in src or "pub/" in src) or any(x in src for x in ("jquery","leaflet","bootstrap","cookie","moment")): continue
                    try:
                        text=urlopen(urljoin(url,src),timeout=15).read().decode("utf-8")
                        print("SCRIPT",src,text[:18000])
                    except Exception as e: print(type(e).__name__,str(e)[:200])
    except Exception as e: print(type(e).__name__,str(e)[:200])

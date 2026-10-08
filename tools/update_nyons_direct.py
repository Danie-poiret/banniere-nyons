import json,re
from urllib.request import Request,urlopen
from datetime import datetime
from zoneinfo import ZoneInfo
def get(url):
    return urlopen(Request(url,headers={"User-Agent":"VivreAnyons/1.0 contact@vivreanyons.fr"}),timeout=20).read().decode("utf-8")
urls={
"air":"https://www.atmo-auvergnerhonealpes.fr/air-commune/Ville/26220/indice-atmo",
"widget":"https://api.atmo-aura.fr/pub/create-widget",
"river":"https://www.vigicrues.gouv.fr/services/observations.json/?CdStationHydro=V533401002&GrdSerie=H&FormatDate=iso",
"fire":"https://www.risque-prevention-incendie.fr/drome",
"massifs":"https://www.risque-prevention-incendie.fr/static/26/js/massifs_prev.js"}
for key,url in urls.items():
    print("\nPROVIDER",key,flush=True)
    try:
        b=get(url)
        if key=="river":
            s=json.loads(b)["Serie"]; print({k:v for k,v in s.items() if k!="ObssHydro"}); print(s["ObssHydro"][-3:])
        elif key=="air":
            from html.parser import HTMLParser
            class Text(HTMLParser):
                def handle_data(self,data):
                    if data.strip(): self.bits.append(data.strip())
            p=Text();p.bits=[];p.feed(b);t="\n".join(p.bits);i=t.find("Qualité de l'air à Nyons");print(t[i:i+3000])
            for marker in ("indice-label", "c-indice", "date-update", "indice-date", "Données mises"):
                i=b.find(marker);print(marker,b[max(0,i-300):i+1000])
            print("HEAD JSON",b[:10000][-6000:])
        elif key=="massifs":print(b[-10000:])
        else:print(b[-16000:])
    except Exception as e:print(type(e).__name__,str(e)[:200])

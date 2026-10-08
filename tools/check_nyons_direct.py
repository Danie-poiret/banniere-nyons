"""Validate adapters, the unchanged forecast, mobile layout and published block."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import copy, json, sys, time
from urllib.request import urlopen
import update_nyons_direct as collector

ROOT = Path(__file__).resolve().parents[1]
def adapter_checks():
    collector.now = datetime(2026,10,8,8,tzinfo=timezone.utc)
    collector.today = collector.now.astimezone(collector.PARIS).date()
    collector.end_day = datetime.combine(collector.today+timedelta(days=1),datetime.min.time(),collector.PARIS)
    def rejected(call):
        try:
            call()
        except (ValueError,KeyError):
            return
        raise AssertionError("Une donnée invalide a été acceptée")
    air = "<h2>Qualité de l'air à Nyons</h2><p>Jeudi 8 Octobre, bulletin du jour.</p><span>Moyen</span><p>Sur les 12 derniers mois</p><p>Données mises à jour le 07/10/2026 - 11:58</p>"
    assert collector.parse_air(air)["label"] == "Indice ATMO : Moyen"
    rejected(lambda:collector.parse_air(air.replace("8 Octobre","7 Octobre")))
    rejected(lambda:collector.parse_air(air.replace("07/10/2026","01/10/2026")))
    rejected(lambda:collector.parse_air(air.replace("Nyons","Lyon")))
    series = {"Serie":{"CdStationHydro":"V533401002","GrdSerie":"H","ObssHydro":[{"DtObsHydro":"2026-10-08T07:00:00Z","ResObsHydro":0.35}]}}
    assert collector.parse_river(json.dumps(series))["heightMetres"] == .35
    missing = copy.deepcopy(series); missing["Serie"]["ObssHydro"][0]["ResObsHydro"] = None
    rejected(lambda:collector.parse_river(json.dumps(missing)))
    stale = json.dumps(series).replace("2026-10-08T07","2026-10-07T07")
    rejected(lambda:collector.parse_river(stale))
    rejected(lambda:collector.parse_river(json.dumps(series).replace("V533401002","WRONG")))
    rejected(lambda:collector.parse_river(json.dumps(series).replace("2026-10-08T07","2026-10-09T07")))
    assert collector.fire_path(["var url_data = '/static/26/import_data_carto/json/';"]) == "/static/26/import_data_carto/json/"
    assert collector.fire_path(["const url_data = '/static/' + id + '/import_data_carto/json/';"]) == "/static/26/import_data_carto/json/"
    rejected(lambda:collector.fire_path(["url_data = unsafe();"]))
    assert collector.parse_fire('{"massifs":{"267":[2,0]}}')["label"] == "Niveau jaune"
    rejected(lambda:collector.parse_fire('{"massifs":{"267":[0,0]}}'))
    rejected(lambda:collector.parse_fire('{"massifs":{"261":[2,0]}}'))
    zone = [{"code":"84_26_0009","type":"SUP","departement":"26","niveauGravite":"alerte","arrete":{"dateDebutValidite":"2026-08-11T00:00:00Z","dateFinValidite":"2026-10-31T00:00:00Z"}}]
    assert collector.parse_water(json.dumps(zone))["label"] == "Alerte"
    rejected(lambda:collector.parse_water("[]"))
    rejected(lambda:collector.parse_water(json.dumps(zone).replace('"SUP"','"AEP"')))
    rejected(lambda:collector.parse_water(json.dumps(zone).replace("2026-10-31","2026-09-30")))
    rejected(lambda:collector.parse_water(json.dumps(zone).replace('"alerte"','null')))
    print("ADAPTERS_OK : dates, station, ressource SUP, niveaux absents et carte non publiée.",flush=True)

def browser_checks(base, published):
    import base64, threading
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
    from functools import partial
    from playwright.sync_api import sync_playwright
    server = None
    if not published:
        server = ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base = "http://127.0.0.1:"+str(server.server_port)
    def read(path):
        with urlopen(base+path,timeout=20) as response:
            assert response.status == 200
            return response.read().decode("utf-8")
    expected = json.loads((ROOT/"assets/nyons-direct.json").read_text())
    for attempt in range(30 if published else 1):
        try:
            html = read("/meteo-nyons/?direct=20261008")
            data = json.loads(read("/assets/nyons-direct.json"))
            assert 'data-nyons-direct' in html and data["collectedAt"] == expected["collectedAt"]
            assert "data-direct-card" in read("/assets/nyons-direct.js")
            break
        except Exception:
            if attempt == (29 if published else 0):
                raise
            time.sleep(10)
    assert html.count('data-nyons-direct') == 1
    assert html.index('data-nyons-weather') < html.index('data-nyons-direct') < html.index('class="meteo-reading"')
    assert data["commune"] == "26220" and len(json.dumps(data).encode()) < 8000
    assert 'class="qa"' in html and 'data-weather-extended="true"' in html
    links = ["https://meteofrance.com/previsions-meteo-france/nyons/26110","https://vigilance.meteofrance.fr/fr/drome","https://www.met.no/en"]
    now = datetime.now(timezone.utc)
    expected_states = {}
    for key,item in data["items"].items():
        expected_states[key] = "available" if item["status"]=="available" and collector.parsed(item["validUntil"])>now else "unavailable"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width":1280,"height":1000},timezone_id="America/Los_Angeles")
        page = context.new_page(); requests = []
        page.on("request",lambda r:requests.append(r.url))
        page.goto(base+"/meteo-nyons/?direct=20261008",wait_until="domcontentloaded")
        page.wait_for_selector('[data-direct-state="ready"]',timeout=20000)
        page.wait_for_selector('[data-weather-state="ready"]',timeout=25000)
        section = page.locator("[data-nyons-direct]")
        assert section.is_visible() and section.locator(".nyons-direct-card").count() == 5
        assert page.locator(".weather-day").count() == 7
        for link in links:
            assert page.locator('.nyons-weather a[href="'+link+'"]').count() == 1
        page.locator('[data-weather-period="10"]').click()
        assert 7 <= page.locator(".weather-day").count() <= 10
        for key,state in expected_states.items():
            card = section.locator('[data-direct-card="'+key+'"]')
            assert card.get_attribute("data-state") == state,(key,card.inner_text())
            if state=="available":
                assert data["items"][key]["label"] == card.locator("[data-direct-value]").inner_text()
        sun = section.locator('[data-direct-card="sun"]')
        assert "Lever" in sun.inner_text() and "coucher" in sun.inner_text() and "Durée du jour" in sun.inner_text()
        assert sun.get_attribute("data-solar-date") == now.astimezone(collector.PARIS).date().isoformat()
        assert sum("nyons-direct.json" in u for u in requests) == 1
        assert not any(host in u for u in requests for host in ("api.atmo","vigicrues.gouv","api.vigieau","risque-prevention-incendie","api.openai"))
        refuse = page.get_by_role("button",name="Refuser",exact=True)
        if refuse.count() and refuse.first.is_visible():
            refuse.first.click()
        pictures = []
        for width in (1280,390,320):
            page.set_viewport_size({"width":width,"height":1000})
            section.scroll_into_view_if_needed();page.wait_for_timeout(150)
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
            assert section.evaluate("(e)=>e.scrollWidth<=e.clientWidth+1")
            for card in section.locator(".nyons-direct-card").all():
                assert card.evaluate("(e)=>e.scrollWidth<=e.clientWidth+1")
            if published and width in (1280,390):
                img=section.screenshot(type="jpeg",quality=70,style="header{visibility:hidden!important}")
                pictures.append({"width":width,"base64":base64.b64encode(img).decode()})
        # Panne JSON : les liens et le calcul solaire restent disponibles.
        page.route("**/assets/nyons-direct.json",lambda route:route.fulfill(status=503,body="Indisponible"))
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector('[data-direct-state="error"]',timeout=20000)
        assert page.locator('.nyons-direct-card[data-state="unavailable"]').count() == 4
        assert page.locator('[data-direct-card="sun"]').get_attribute("data-state") == "available"
        # Un vieux statut ne doit jamais être présenté comme actuel.
        page.unroute("**/assets/nyons-direct.json")
        old=copy.deepcopy(data)
        for item in old["items"].values():
            item.update(status="available",label="FAUX STATUT ANCIEN",validUntil="2020-01-01T00:00:00Z",checkedAt="2020-01-01T00:00:00Z")
        page.route("**/assets/nyons-direct.json",lambda route:route.fulfill(status=200,content_type="application/json",body=json.dumps(old)))
        page.reload(wait_until="domcontentloaded");page.wait_for_selector('[data-direct-state="ready"]')
        assert "FAUX STATUT ANCIEN" not in page.locator("[data-nyons-direct]").inner_text()
        # Date française même avec un navigateur étranger et au changement d'heure.
        page.unroute("**/assets/nyons-direct.json")
        for moment,day,hour in (("2026-03-28T12:00:00Z","2026-03-28","06"),("2026-03-29T12:00:00Z","2026-03-29","07"),("2026-06-21T12:00:00Z","2026-06-21","05"),("2026-12-21T12:00:00Z","2026-12-21","08"),("2026-10-08T22:30:00Z","2026-10-09","07")):
            solar_context=browser.new_context(timezone_id="America/Los_Angeles")
            solar_page=solar_context.new_page()
            solar_page.clock.install(time=datetime.fromisoformat(moment.replace("Z","+00:00")))
            solar_page.goto(base+"/meteo-nyons/",wait_until="domcontentloaded")
            solar_page.wait_for_selector('[data-direct-card="sun"][data-state="available"]')
            solar=solar_page.locator('[data-direct-card="sun"]')
            assert solar.get_attribute("data-solar-date")==day
            assert ("Lever "+hour+":") in solar.inner_text(),(day,solar.inner_text())
            solar_context.close()
        plain=browser.new_context(java_script_enabled=False)
        plainpage=plain.new_page();plainpage.goto(base+"/meteo-nyons/",wait_until="domcontentloaded")
        assert plainpage.locator("[data-nyons-direct]").is_visible()
        assert plainpage.locator("[data-nyons-direct] a").count()==4
        browser.close()
    if server:
        server.shutdown()
    print(("PUBLISHED_OK" if published else "LOCAL_OK")+": météo conservée, 5 cartes visibles, un JSON, 1280/390/320 px, pannes et péremption, heure française et changement d'heure.",flush=True)
    if published:
        print("DIRECT_SCREENSHOTS_BEGIN",flush=True)
        print(json.dumps(pictures),flush=True)
        print("DIRECT_SCREENSHOTS_END",flush=True)
        print("PUBLIC_VALUES",json.dumps({k:{"status":v["status"],"label":v["label"],"detail":v.get("detail")} for k,v in data["items"].items()},ensure_ascii=False),flush=True)

if __name__ == "__main__":
    if "--adapters" in sys.argv:
        adapter_checks()
    else:
        browser_checks("https://www.vivreanyons.fr","--published" in sys.argv)

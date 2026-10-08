"""Check real published data, rendering, refresh, failures and small screens."""
from datetime import datetime, timedelta, timezone
import base64
import copy
import json
import math
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

BASE = "https://www.vivreanyons.fr"
def read(url):
    with urlopen(url, timeout=20) as response:
        assert response.status == 200
        return response.read().decode("utf-8")
for attempt in range(24):
    try:
        html = read(BASE + "/")
        forecast = json.loads(read(BASE + "/assets/meteo-nyons.json"))
        if 'data-nyons-weather' in html and forecast.get("location") == "Nyons" and 'data-weather-extended' in read(BASE + '/meteo-nyons/') and 'data-weather-compact' in html and 'pont-roman-nyons-ciel-bleu.png' in read(BASE + '/meteo-nyons/'):
            break
    except Exception:
        pass
    time.sleep(10)
else:
    raise AssertionError("Le module météo ou ses données ne sont pas encore publiés")

assert forecast["provider"] == "MET Norway"
assert forecast["timezone"] == "Europe/Paris"
assert forecast["units"]["air_temperature"] == "celsius"
assert forecast["units"]["wind_speed"] == "m/s"
assert len(forecast["timeseries"]) >= 20
for prefix in ("", "/vivreanyons-test", "/banniere-nyons/vivreanyons-test"):
    source = read(BASE + prefix + "/")
    assert source.count("data-nyons-weather") == 1
    assert 'data-latest-article=' in source and 'href="' + prefix + '/meteo-nyons/"' in source
    assert "nyons-weather" in read(BASE + prefix + "/assets/meteo-nyons.css")
    assert "Europe/Paris" in read(BASE + prefix + "/assets/meteo-nyons.js")
    assert json.loads(read(BASE + prefix + "/assets/meteo-nyons.json"))["provider"] == "MET Norway"
print("Météo publique : trois accueils, styles, scripts et prévisions accessibles.", flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={"width":1280,"height":1000}, timezone_id="America/Los_Angeles")
    page = context.new_page()
    weather_requests = []
    page.on("request", lambda request: weather_requests.append(request.url) if "meteo" in request.url else None)
    page.goto(BASE + "/#meteo-nyons", wait_until="domcontentloaded")
    module = page.locator("[data-nyons-weather]")
    page.wait_for_selector('[data-weather-state="ready"]', timeout=25000)
    refuse = page.get_by_role("button", name="Refuser", exact=True)
    if refuse.count() and refuse.first.is_visible():
        refuse.first.click()
    assert module.locator(".weather-day").count() == 5
    assert "°C" in module.locator("[data-weather-temp]").inner_text()
    current = min(forecast["timeseries"], key=lambda point: abs(datetime.fromisoformat(point["time"].replace("Z","+00:00")).timestamp()-time.time()))
    expected = math.floor(current["data"]["instant"]["details"]["air_temperature"] + 0.5)
    assert module.locator("[data-weather-temp]").inner_text() == str(expected) + " °C"
    france_day = page.evaluate("new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())")
    first_day = module.locator(".weather-day time").first.get_attribute("datetime")
    assert first_day == france_day, (first_day, france_day)
    assert module.locator(".weather-day time").first.inner_text() == "Aujourd’hui"
    page.locator("[data-weather-refresh]").focus()
    page.keyboard.press("Enter")
    page.wait_for_function("document.querySelector('[data-nyons-weather]').getAttribute('aria-busy') === 'false'")
    assert module.get_attribute("data-weather-state") == "ready"
    assert module.get_attribute("data-weather-compact") == "true"
    for route in ("/", "/infos-pratiques-nyons/", "/nyons-image-1/", "/que-faire-nyons/Pont-Roman-de-Nyons/", "/vivreanyons-test/infos-pratiques-nyons/", "/banniere-nyons/vivreanyons-test/infos-pratiques-nyons/"):
        source = read(BASE + route)
        prefix = "/banniere-nyons/vivreanyons-test" if route.startswith("/banniere-nyons/") else "/vivreanyons-test" if route.startswith("/vivreanyons-test/") else ""
        assert '<a data-weather-nav="direct" href="' + prefix + '/meteo-nyons/"' in source

    images=[]
    for width in (1280,390,320):
        page.set_viewport_size({"width":width,"height":1100})
        page.wait_for_timeout(250)
        bounds = module.bounding_box()
        assert bounds["x"] >= -1 and bounds["x"] + bounds["width"] <= width+1
        assert module.evaluate("(element) => element.scrollWidth <= element.clientWidth + 1")
        for selector in (".weather-now",".weather-day",".weather-heading",".weather-footer"):
            for element in module.locator(selector).all():
                if not element.is_visible():
                    continue
                box = element.bounding_box()
                assert box["x"] >= bounds["x"]-1 and box["x"]+box["width"] <= bounds["x"]+bounds["width"]+1, (width,selector,box)
        if width in (1280,390):
            screenshot = module.screenshot(type="jpeg", quality=65, style="header { visibility: hidden !important; }")
            images.append({"width":width,"base64":base64.b64encode(screenshot).decode("ascii")})
    assert not any("api.met.no" in url or "api.open-meteo" in url for url in weather_requests)

    # Simulate a service failure, then restore the actual retrieved forecast.
    error_context = browser.new_context(viewport={"width":390,"height":1000})
    error_page = error_context.new_page()
    mode = {"data":None}
    def fulfill(route):
        if mode["data"] is None:
            route.fulfill(status=503, body="Indisponible")
        else:
            route.fulfill(status=200, content_type="application/json", body=json.dumps(mode["data"]))
    error_page.route("**/assets/meteo-nyons.json", fulfill)
    error_page.goto(BASE + "/#meteo-nyons", wait_until="domcontentloaded")
    error_page.wait_for_selector('[data-weather-state="error"]')
    assert not error_page.locator("[data-weather-content]").is_visible()
    assert error_page.locator("[data-weather-refresh]").is_enabled()
    mode["data"] = forecast
    error_page.locator("[data-weather-refresh]").click()
    error_page.wait_for_selector('[data-weather-state="ready"]')
    assert error_page.locator(".weather-day").count() == 5

    # Missing optional values must be a dash, never a fabricated zero.
    mode["data"] = copy.deepcopy(forecast)
    for point in mode["data"]["timeseries"]:
        point["data"]["instant"]["details"]["wind_speed"] = None
        point["data"]["instant"]["details"]["relative_humidity"] = None
    error_page.locator("[data-weather-refresh]").click()
    error_page.wait_for_function("document.querySelector('[data-weather-wind]').textContent === '—'")
    assert error_page.locator("[data-weather-humidity]").inner_text() == "—"

    for case in ("expired", "empty", "missing-temperature"):
        data = copy.deepcopy(forecast)
        if case == "expired":
            data["collectedAt"] = (datetime.now(timezone.utc)-timedelta(days=2)).isoformat()
        elif case == "empty":
            data["timeseries"] = []
        else:
            for point in data["timeseries"]:
                point["data"]["instant"]["details"]["air_temperature"] = None
        mode["data"] = data
        error_page.locator("[data-weather-refresh]").click()
        error_page.wait_for_selector('[data-weather-state="error"]')
        assert not error_page.locator("[data-weather-content]").is_visible()

    plain = browser.new_context(java_script_enabled=False)
    plain_page = plain.new_page()
    plain_page.goto(BASE + "/#meteo-nyons", wait_until="domcontentloaded")
    assert plain_page.locator(".nyons-weather noscript").is_visible()
    assert plain_page.locator('.nyons-weather a[href="/meteo-nyons/"]').is_visible()
    assert not plain_page.locator("[data-weather-refresh]").is_visible()

    for prefix in ("", "/vivreanyons-test", "/banniere-nyons/vivreanyons-test"):
        source = read(BASE + prefix + "/meteo-nyons/")
        assert source.count("<h1>") == 1
        assert "Météo à Nyons : aujourd’hui, demain, prévisions et climat toute l’année" in source
        assert 'href="https://www.vivreanyons.fr/meteo-nyons/"' in source
        assert '"datePublished":"2026-10-08"' in source
        assert '"@type":"FAQPage"' in source and source.count('class="qa"') == 7
        assert "Sources et liens utiles" in source and "Pontias" in source and "mistral" in source
        assert "météo de Nyons à 15 jours" in source and "mois prochain" in source
        assert "parfois incomplet" in source and "chiffres inventés" in source
        assert 'data-weather-extended="true"' in source
        assert source.count('<table class="meteo-table">') == 3
        assert 'href="' + prefix + '/meteo-nyons/"' in read(BASE + prefix + "/infos-pratiques-nyons/")
        assert 'href="' + prefix + '/meteo-nyons/"' in read(BASE + prefix + "/toutes-les-pages/")
    assert "<loc>https://www.vivreanyons.fr/meteo-nyons/</loc>" in read(BASE + "/sitemap.xml")
    detail_page = context.new_page()
    detail_page.goto(BASE + "/meteo-nyons/?photo=20261008", wait_until="domcontentloaded")
    detail_page.wait_for_selector('[data-weather-state="ready"]', timeout=25000)
    refuse = detail_page.get_by_role("button", name="Refuser", exact=True)
    if refuse.count() and refuse.first.is_visible():
        refuse.first.click()
    detail = detail_page.locator("[data-nyons-weather]")
    assert detail.locator(".weather-day").count() == 7
    detail.locator('[data-weather-period="10"]').click()
    assert 7 <= detail.locator(".weather-day").count() <= 10
    assert detail.locator('[data-weather-period="10"]').get_attribute("aria-pressed") == "true"
    assert "Dernier créneau disponible" in detail.locator("[data-weather-horizon]").inner_text()
    detail.locator('[data-weather-period="weekend"]').click()
    assert 1 <= detail.locator(".weather-day").count() <= 2
    for element in detail.locator(".weather-day time").all():
        date = datetime.fromisoformat(element.get_attribute("datetime"))
        assert date.weekday() in (5, 6)
    detail.locator('[data-weather-period="7"]').focus()
    detail_page.keyboard.press("Enter")
    assert detail.locator(".weather-day").count() == 7
    detail.locator(".weather-hourly summary").click()
    assert 1 <= detail.locator("[data-weather-hours] tr").count() <= 24
    assert "mm / 1 h" in detail.locator("[data-weather-hours]").inner_text()
    photo = detail_page.locator('img[src$="/assets/photos/meteo-nyons/pont-roman-nyons-ciel-bleu.png"]')
    photo.scroll_into_view_if_needed()
    detail_page.wait_for_function("""document.querySelector('img[src$="/assets/photos/meteo-nyons/pont-roman-nyons-ciel-bleu.png"]').naturalWidth > 0""")
    print("Photo météo fournie :", photo.evaluate("(image) => ({src:image.currentSrc,width:image.naturalWidth,height:image.naturalHeight})"), flush=True)
    assert photo.evaluate("(image) => image.naturalWidth === 495 && image.naturalHeight === 305")
    detail_page.set_viewport_size({"width":1280,"height":1000})
    detail.locator(".weather-hourly summary").click()
    images.append({"width":1280,"page":"meteo-nyons","base64":base64.b64encode(detail.screenshot(type="jpeg", quality=65, style="header {visibility:hidden!important}")).decode("ascii")})
    for width in (390,320):
        detail_page.set_viewport_size({"width":width,"height":1000})
        detail_page.wait_for_timeout(150)
        assert detail.evaluate("(element) => element.scrollWidth <= element.clientWidth + 1")
        assert detail_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    print("Page météo Nyons vérifiée : SEO et liens, 7/10 jours, week-end, horaires, photo complète, FAQ, sitemap, mobile et accueil préservé.", flush=True)

    browser.close()
print("Météo vérifiée : cinq jours, heure française, températures réelles du modèle, actualisation clavier, absence de débordement à 1280/390/320 px, panne et reprise, valeurs absentes, données périmées, accès sans JavaScript.", flush=True)
print("WEATHER_SCREENSHOTS_BEGIN")
print(json.dumps(images))
print("WEATHER_SCREENSHOTS_END")

# Vérification après publication de la page météo et des vues détaillées.

# Vérification de la photographie du Pont Roman fournie par l’utilisateur.

# Vérification du bandeau compact, du menu Météo et de la photo fournie.

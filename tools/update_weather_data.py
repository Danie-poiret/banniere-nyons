"""Retrieve one shared Nyons forecast; visitors never contact the weather provider."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=44.36&lon=5.14"
ROOT = Path(__file__).resolve().parents[1]
PATHS = [ROOT / prefix / "assets/meteo-nyons.json" for prefix in ("", "vivreanyons-test", "banniere-nyons/vivreanyons-test")]
now = datetime.now(timezone.utc)
if PATHS[0].exists():
    try:
        previous = json.loads(PATHS[0].read_text(encoding="utf-8"))
        expires = datetime.fromisoformat(previous["expiresAt"].replace("Z", "+00:00"))
        if expires > now and all(path.exists() for path in PATHS):
            print("Prévisions Nyons encore valides ; aucune requête supplémentaire.")
            raise SystemExit(0)
    except (ValueError, KeyError, TypeError):
        pass
request = Request(URL, headers={"User-Agent": "VivreAnyons-Meteo/1.0 https://www.vivreanyons.fr/ contact@vivreanyons.fr"})
with urlopen(request, timeout=30) as response:
    raw = json.load(response)
    expires_header = response.headers.get("Expires")
properties = raw["properties"]
units = properties["meta"]["units"]
assert units["air_temperature"] == "celsius" and units["wind_speed"] == "m/s", "Unexpected units"
series = properties["timeseries"]
assert len(series) >= 20, "Incomplete forecast"
assert any(isinstance(item["data"]["instant"]["details"].get("air_temperature"), (int, float)) for item in series), "Missing temperatures"
model_time = datetime.fromisoformat(properties["meta"]["updated_at"].replace("Z", "+00:00"))
assert abs((now - model_time).total_seconds()) < 36 * 3600, "Outdated model"
forecast = {
    "location": "Nyons",
    "latitude": 44.36,
    "longitude": 5.14,
    "timezone": "Europe/Paris",
    "provider": "MET Norway",
    "license": "CC BY 4.0",
    "collectedAt": now.isoformat().replace("+00:00", "Z"),
    "modelUpdatedAt": properties["meta"]["updated_at"],
    "expiresAt": parsedate_to_datetime(expires_header).isoformat().replace("+00:00", "Z") if expires_header else now.isoformat().replace("+00:00", "Z"),
    "units": units,
    "timeseries": series
}
content = json.dumps(forecast, ensure_ascii=False, separators=(",", ":")) + "\n"
for path in PATHS:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
print("Prévisions Nyons récupérées :", len(series), "créneaux ; modèle du", forecast["modelUpdatedAt"])

"""
Integrazione Open-Meteo per la dashboard.

Nessuna API key richiesta. Documentazione: https://open-meteo.com/en/docs

Nota ambiente: questo modulo richiede accesso a internet. Nel sandbox di
sviluppo di Claude la rete e' disabilitata, quindi 'get_weather()' qui
fallisce e viene usato il fallback con dati di esempio (utile solo per
continuare a lavorare sul layout). Sul tuo PC, o nel job cloud schedulato
(es. GitHub Actions) che genera l'immagine per il device, la rete c'e'
normalmente e la funzione restituira' i dati reali.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime

LAT, LON = 38.1389, 14.9653  # Patti (ME)
LOCATION_LABEL = "Patti (ME)"

API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,weather_code"
    "&hourly=temperature_2m,weather_code"
    "&daily=temperature_2m_max,temperature_2m_min,weather_code"
    "&timezone=Europe%2FRome"
    "&forecast_days=6"
)

# Mappa codici WMO (weather_code) -> (etichetta italiana, tipo icona)
# tipo icona: sun | sun_cloud | cloud | rain | snow
WMO_MAP = {
    0: ("Sereno", "sun"),
    1: ("Prevalentemente sereno", "sun_cloud"),
    2: ("Poco nuvoloso", "sun_cloud"),
    3: ("Nuvoloso", "cloud"),
    45: ("Nebbia", "cloud"),
    48: ("Nebbia con brina", "cloud"),
    51: ("Pioviggine debole", "rain"),
    53: ("Pioviggine", "rain"),
    55: ("Pioviggine intensa", "rain"),
    56: ("Pioviggine gelata", "rain"),
    57: ("Pioviggine gelata intensa", "rain"),
    61: ("Pioggia debole", "rain"),
    63: ("Pioggia", "rain"),
    65: ("Pioggia intensa", "rain"),
    66: ("Pioggia gelata", "rain"),
    67: ("Pioggia gelata intensa", "rain"),
    71: ("Neve debole", "snow"),
    73: ("Neve", "snow"),
    75: ("Neve intensa", "snow"),
    77: ("Graupel", "snow"),
    80: ("Rovesci deboli", "rain"),
    81: ("Rovesci", "rain"),
    82: ("Rovesci intensi", "rain"),
    85: ("Rovesci di neve deboli", "snow"),
    86: ("Rovesci di neve", "snow"),
    95: ("Temporale", "rain"),
    96: ("Temporale con grandine", "rain"),
    99: ("Temporale con grandine forte", "rain"),
}

def wmo_lookup(code):
    return WMO_MAP.get(code, ("N/D", "cloud"))


def _fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "dashboard-citofono/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def get_weather():
    """Ritorna un dict con current/hourly/daily pronto per il rendering.
    Solleva RuntimeError se la chiamata di rete fallisce (gestito da chi
    chiama, che puo' decidere di usare i dati di esempio come fallback).
    """
    try:
        data = _fetch_json(API_URL)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise RuntimeError(f"Impossibile contattare Open-Meteo: {e}")

    current = data["current"]
    cur_label, cur_icon = wmo_lookup(current["weather_code"])

    daily = data["daily"]
    today_max = round(daily["temperature_2m_max"][0])
    today_min = round(daily["temperature_2m_min"][0])

    # Prossime 5 ore utili (a partire dall'ora corrente, incluso "Ora")
    now_iso = data["current"]["time"]  # es. 2026-09-26T18:45
    hourly_times = data["hourly"]["time"]
    hourly_temp = data["hourly"]["temperature_2m"]
    hourly_code = data["hourly"]["weather_code"]

    try:
        start_idx = hourly_times.index(
            [t for t in hourly_times if t >= now_iso][0]
        )
    except IndexError:
        start_idx = 0

    hourly = []
    for i in range(start_idx, min(start_idx + 5, len(hourly_times))):
        t = hourly_times[i]
        label = "Ora" if i == start_idx else t[11:16]  # HH:MM
        _, icon = wmo_lookup(hourly_code[i])
        hourly.append((label, round(hourly_temp[i]), icon))

    # Prossimi 5 giorni (indice 0 = oggi)
    day_labels_it = ["Oggi", "Dom", "Lun", "Mar", "Mer", "Gio", "Ven", "Sab"]
    daily_out = []
    for i in range(min(5, len(daily["time"]))):
        if i == 0:
            label = "Oggi"
        else:
            dt = datetime.strptime(daily["time"][i], "%Y-%m-%d")
            label = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"][dt.weekday()]
        _, icon = wmo_lookup(daily["weather_code"][i])
        lo = round(daily["temperature_2m_min"][i])
        hi = round(daily["temperature_2m_max"][i])
        daily_out.append((label, lo, hi, icon))

    return {
        "current_temp": round(current["temperature_2m"]),
        "current_label": cur_label,
        "current_icon": cur_icon,
        "today_min": today_min,
        "today_max": today_max,
        "hourly": hourly,
        "daily": daily_out,
        "location": LOCATION_LABEL,
    }


# Dati di fallback identici allo stile usato finora, usati solo se la
# rete non e' disponibile (utile in questo ambiente di sviluppo).
FALLBACK = {
    "current_temp": 24,
    "current_label": "Poco nuvoloso",
    "current_icon": "sun_cloud",
    "today_min": 18,
    "today_max": 25,
    "hourly": [
        ("Ora", 24, "sun_cloud"),
        ("20:00", 22, "sun"),
        ("21:00", 20, "cloud"),
        ("22:00", 19, "cloud"),
        ("23:00", 18, "rain"),
    ],
    "daily": [
        ("Oggi", 18, 25, "sun_cloud"),
        ("Dom", 17, 26, "sun"),
        ("Lun", 17, 24, "sun"),
        ("Mar", 16, 22, "cloud"),
        ("Mer", 15, 20, "rain"),
    ],
    "location": LOCATION_LABEL,
}


def get_weather_safe():
    """Prova a prendere dati reali, altrimenti usa il fallback (con un avviso)."""
    try:
        return get_weather(), True
    except RuntimeError as e:
        print(f"[weather] {e} -> uso dati di esempio")
        return FALLBACK, False


if __name__ == "__main__":
    w, live = get_weather_safe()
    print("Dati live:" if live else "Dati fallback:")
    print(json.dumps(w, indent=2, ensure_ascii=False))

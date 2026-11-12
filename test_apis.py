"""Test rapide des deux sources du projet DataOps (sujet Énergie).

Usage :
    pip install requests
    python test_apis.py

Le script ne modifie rien : il interroge les APIs, affiche le statut HTTP,
les colonnes reçues et quelques lignes, pour valider l'accès avant de concevoir.
"""
import json
import sys

import requests

ODRE = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets"
METEO = "https://archive-api.open-meteo.com/v1/archive"
TIMEOUT = 30


def test_eco2mix(dataset: str) -> bool:
    url = f"{ODRE}/{dataset}/records"
    params = {"limit": 3, "order_by": "date_heure desc", "timezone": "Europe/Paris"}
    print(f"\n=== eCO2mix : {dataset} ===")
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        print("ECHEC réseau :", e)
        return False
    print("Statut HTTP :", r.status_code)
    if r.status_code != 200:
        print(r.text[:300])
        return False
    data = r.json()
    print("Nombre total de lignes (total_count) :", data.get("total_count"))
    rows = data.get("results", [])
    if not rows:
        print("Aucune ligne renvoyée.")
        return False
    print("Colonnes :", sorted(rows[0].keys()))
    print("Exemple :", json.dumps(rows[0], ensure_ascii=False)[:400])
    return True


def test_open_meteo() -> bool:
    params = {
        "latitude": 48.8566,   # Paris
        "longitude": 2.3522,
        "start_date": "2026-10-01",
        "end_date": "2026-10-03",
        "hourly": "temperature_2m,shortwave_radiation",
        "timezone": "Europe/Paris",
    }
    print("\n=== Open-Meteo (archive) ===")
    try:
        r = requests.get(METEO, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        print("ECHEC réseau :", e)
        return False
    print("Statut HTTP :", r.status_code)
    if r.status_code != 200:
        print(r.text[:300])
        return False
    hourly = r.json().get("hourly", {})
    print("Colonnes :", list(hourly.keys()))
    print("Nombre d'heures reçues :", len(hourly.get("time", [])))
    print("Première heure :", hourly["time"][0], "->",
          hourly["temperature_2m"][0], "°C,",
          hourly["shortwave_radiation"][0], "W/m2")
    return True


if __name__ == "__main__":
    results = {
        "eco2mix-national-tr": test_eco2mix("eco2mix-national-tr"),
        "eco2mix-national-cons-def": test_eco2mix("eco2mix-national-cons-def"),
        "open-meteo": test_open_meteo(),
    }
    print("\n=== Bilan ===")
    for name, ok in results.items():
        print(f"{'OK  ' if ok else 'ECHEC'}  {name}")
    sys.exit(0 if all(results.values()) else 1)

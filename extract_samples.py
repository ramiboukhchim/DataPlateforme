"""Extrait de petits échantillons CSV des trois sources, pour que l'équipe
puisse travailler sans attendre le chargement complet.

Usage (depuis la racine du dépôt) :
    pip install requests
    python extract_samples.py

Produit dans tests/fixtures/ :
    eco2mix_cons_def_sample.csv   (11 jours en janvier 2025, ~1 000 lignes)
    eco2mix_tr_sample.csv         (les ~1 000 lignes les plus récentes)
    meteo_sample.csv              (mêmes 11 jours, météo horaire Paris)

Peu d'appels (une dizaine par jeu) pour rester loin du quota ODRE.
"""
import csv
import sys
from pathlib import Path

import requests

ODRE = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets"
METEO = "https://archive-api.open-meteo.com/v1/archive"
OUT = Path("tests/fixtures")
PAGE = 100          # taille de page maximale de l'API de records
TARGET = 1000       # nombre de lignes visé par échantillon
TIMEOUT = 30


def fetch_records(dataset, where=None, order_by="date_heure asc"):
    rows, offset = [], 0
    while len(rows) < TARGET:
        params = {
            "limit": PAGE,
            "offset": offset,
            "order_by": order_by,
            "timezone": "Europe/Paris",
        }
        if where:
            params["where"] = where
        r = requests.get(f"{ODRE}/{dataset}/records", params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            sys.exit(f"ERREUR {dataset} (HTTP {r.status_code}) : {r.text[:300]}")
        batch = r.json().get("results", [])
        if not batch:
            break
        rows.extend(batch)
        offset += PAGE
    return rows[:TARGET]


def write_csv(path, rows):
    cols = sorted({k for row in rows for k in row})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"écrit : {path} ({len(rows)} lignes, {len(cols)} colonnes)")


def fetch_meteo(start, end):
    params = {
        "latitude": 48.8566,
        "longitude": 2.3522,
        "start_date": start,
        "end_date": end,
        "hourly": "temperature_2m,shortwave_radiation",
        "timezone": "Europe/Paris",
    }
    r = requests.get(METEO, params=params, timeout=TIMEOUT)
    if r.status_code != 200:
        sys.exit(f"ERREUR Open-Meteo (HTTP {r.status_code}) : {r.text[:300]}")
    h = r.json()["hourly"]
    return [
        {"time": t, "temperature_2m": a, "shortwave_radiation": b}
        for t, a, b in zip(h["time"], h["temperature_2m"], h["shortwave_radiation"])
    ]


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    print("1/3 eCO2mix cons-def (janvier 2025)...")
    write_csv(
        OUT / "eco2mix_cons_def_sample.csv",
        fetch_records(
            "eco2mix-national-cons-def",
            where="date_heure >= date'2025-01-01' and date_heure < date'2025-01-12'",
        ),
    )

    print("2/3 eCO2mix tr (les plus récentes)...")
    write_csv(
        OUT / "eco2mix_tr_sample.csv",
        fetch_records("eco2mix-national-tr", order_by="date_heure desc"),
    )

    print("3/3 Open-Meteo (mêmes 11 jours)...")
    write_csv(OUT / "meteo_sample.csv", fetch_meteo("2025-01-01", "2025-01-11"))

    print("\nTerminé. Vérifiez les fichiers puis : git add tests/fixtures")

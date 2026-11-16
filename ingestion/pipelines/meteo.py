"""Ingestion météo (Open-Meteo, archive) vers DuckDB avec dlt.

Charge la table raw.meteo_horaire : une ligne par heure, une ville.

Principes (identiques au pipeline eCO2mix) :
  * Chargement par FENÊTRE DE DATES (start inclus, end exclu), découpée par année.
  * Mode `merge` : relancer une fenêtre ne crée aucun doublon (idempotence).
  * Horodatages en UTC (fuseau par défaut d'Open-Meteo, sans décalage) : pas
    d'ambiguïté aux changements d'heure (ADR-002). La colonne `time` est donc
    de l'UTC, sans suffixe, ex. "2025-01-01T00:00".
  * La ville vient des variables d'environnement METEO_LATITUDE / METEO_LONGITUDE
    (Paris par défaut). Latitude et longitude sont stockées dans la table,
    ce qui permettra d'ajouter des villes sans changer le schéma.

Usage :
    python -m ingestion.pipelines.meteo
    python -m ingestion.pipelines.meteo --start 2012-01-01 --end 2026-11-10
"""
import argparse
import os
from datetime import date, timedelta
from pathlib import Path

import dlt
from dlt.sources.helpers import requests

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
HOURLY = ("temperature_2m", "shortwave_radiation")
PRIMARY_KEY = ("time", "latitude", "longitude")
DEFAULT_DB = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")
LATITUDE = float(os.getenv("METEO_LATITUDE", "48.8566"))
LONGITUDE = float(os.getenv("METEO_LONGITUDE", "2.3522"))
# L'archive a quelques jours de retard : on évite de demander les derniers jours.
ARCHIVE_LAG_DAYS = 6


def year_windows(start: date, end: date):
    """Découpe [start, end) en fenêtres annuelles (début inclus, fin exclue)."""
    cur = start
    while cur < end:
        nxt = date(cur.year + 1, 1, 1)
        yield cur, min(nxt, end)
        cur = nxt


def fetch_hourly(lat: float, lon: float, win_start: date, win_end: date) -> list[dict]:
    """Une requête pour [win_start, win_end) ; l'API veut une date de fin INCLUSE."""
    r = requests.get(
        ARCHIVE,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": win_start.isoformat(),
            "end_date": (win_end - timedelta(days=1)).isoformat(),
            "hourly": ",".join(HOURLY),
        },
        timeout=60,
    )
    r.raise_for_status()
    hourly = r.json().get("hourly")
    if not hourly or "time" not in hourly:
        raise TypeError(f"Réponse inattendue d'Open-Meteo : {str(r.json())[:200]}")
    return [
        {
            "time": t,
            "latitude": lat,
            "longitude": lon,
            **{name: hourly[name][i] for name in HOURLY},
        }
        for i, t in enumerate(hourly["time"])
    ]


@dlt.resource(name="meteo_horaire", write_disposition="merge", primary_key=PRIMARY_KEY)
def meteo_resource(start: date, end: date, lat: float = LATITUDE, lon: float = LONGITUDE):
    for w_start, w_end in year_windows(start, end):
        rows = fetch_hourly(lat, lon, w_start, w_end)
        print(f"meteo: {w_start} -> {w_end} : {len(rows)} lignes")
        yield rows


@dlt.source(name="meteo")
def meteo_source(start: date, end: date, lat: float = LATITUDE, lon: float = LONGITUDE):
    return meteo_resource(start, end, lat, lon)


def run(start: date, end: date, db_path: str = DEFAULT_DB, pipelines_dir: str | None = None):
    """Charge la météo pour la fenêtre [start, end)."""
    db = Path(db_path).resolve()
    db.parent.mkdir(parents=True, exist_ok=True)
    pipeline = dlt.pipeline(
        pipeline_name="meteo",
        destination=dlt.destinations.duckdb(credentials=str(db)),
        dataset_name="raw",
        pipelines_dir=pipelines_dir,
    )
    info = pipeline.run(meteo_source(start, end))
    print(info)
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=date.fromisoformat,
                    default=date.today() - timedelta(days=ARCHIVE_LAG_DAYS + 7))
    ap.add_argument("--end", type=date.fromisoformat,
                    default=date.today() - timedelta(days=ARCHIVE_LAG_DAYS),
                    help="exclu ; par défaut on s'arrête avant les derniers jours (retard de l'archive)")
    ap.add_argument("--db", default=DEFAULT_DB)
    a = ap.parse_args()
    run(a.start, a.end, db_path=a.db)

"""Ingestion eCO2mix (ODRE) vers DuckDB avec dlt.

Deux jeux sont chargés dans le schéma `raw` :
    eco2mix-national-cons-def -> raw.eco2mix_national_cons_def  (historique)
    eco2mix-national-tr       -> raw.eco2mix_national_tr        (récent)

Principes :
  * Chargement par FENÊTRE DE DATES (start inclus, end exclu), découpée par mois.
    Le flow quotidien recharge une courte fenêtre récente ; le backfill passe
    une grande plage. C'est la même fonction dans les deux cas.
  * Mode `merge` avec clé (date_heure, perimetre) : relancer la même fenêtre
    ne crée AUCUN doublon (idempotence) et met à jour les lignes qui changent
    (ex. une prévision devenue mesure, ou "temps réel" devenu "consolidé").
  * Les horodatages sont conservés tels que fournis (Europe/Paris, avec
    décalage). La conversion en UTC se fait au staging (ADR-002).

Usage :
    python -m ingestion.pipelines.eco2mix --dataset tr
    python -m ingestion.pipelines.eco2mix --dataset cons-def --start 2025-01-01 --end 2025-02-01
"""
import argparse
import os
from datetime import date, timedelta
from pathlib import Path

import dlt
from dlt.sources.helpers import requests

ODRE = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets"
DATASETS = {
    "cons-def": "eco2mix-national-cons-def",
    "tr": "eco2mix-national-tr",
}
PRIMARY_KEY = ("date_heure", "perimetre")
DEFAULT_DB = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")


def month_windows(start: date, end: date):
    """Découpe [start, end) en fenêtres mensuelles (début inclus, fin exclue)."""
    cur = start
    while cur < end:
        nxt = date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
        yield cur, min(nxt, end)
        cur = nxt


def fetch_export(dataset_id: str, win_start: date, win_end: date) -> list[dict]:
    """Télécharge une fenêtre via l'endpoint d'EXPORT (un seul appel par fenêtre).

    L'export évite des centaines d'appels paginés (quota ODRE) et la limite
    de pagination de l'API de records.
    """
    where = (
        f"date_heure >= date'{win_start.isoformat()}' "
        f"and date_heure < date'{win_end.isoformat()}'"
    )
    r = requests.get(
        f"{ODRE}/{dataset_id}/exports/json",
        params={"where": where, "order_by": "date_heure asc", "timezone": "Europe/Paris"},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise ValueError(f"Réponse inattendue de l'export {dataset_id}: {type(data)}")
    return data


def _make_resource(dataset_key: str, start: date, end: date):
    dataset_id = DATASETS[dataset_key]

    @dlt.resource(
        name=dataset_id.replace("-", "_"),
        write_disposition="merge",
        primary_key=PRIMARY_KEY,
    )
    def resource():
        for w_start, w_end in month_windows(start, end):
            rows = fetch_export(dataset_id, w_start, w_end)
            print(f"{dataset_id}: {w_start} -> {w_end} : {len(rows)} lignes")
            yield rows

    return resource


@dlt.source(name="eco2mix")
def eco2mix_source(datasets: list[str], start: date, end: date):
    return [_make_resource(d, start, end) for d in datasets]


def run(
    datasets: list[str],
    start: date,
    end: date,
    db_path: str = DEFAULT_DB,
    pipelines_dir: str | None = None,
):
    """Charge les jeux demandés pour la fenêtre [start, end)."""
    db = Path(db_path).resolve()
    db.parent.mkdir(parents=True, exist_ok=True)
    pipeline = dlt.pipeline(
        pipeline_name="eco2mix",
        destination=dlt.destinations.duckdb(credentials=str(db)),
        dataset_name="raw",
        pipelines_dir=pipelines_dir,
    )
    info = pipeline.run(eco2mix_source(datasets, start, end))
    print(info)
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=[*DATASETS, "all"], default="tr")
    ap.add_argument("--start", type=date.fromisoformat, default=date.today() - timedelta(days=7))
    ap.add_argument("--end", type=date.fromisoformat, default=date.today() + timedelta(days=2),
                    help="exclu ; par défaut après-demain pour inclure les prévisions de demain")
    ap.add_argument("--db", default=DEFAULT_DB)
    a = ap.parse_args()
    keys = list(DATASETS) if a.dataset == "all" else [a.dataset]
    run(keys, a.start, a.end, db_path=a.db)

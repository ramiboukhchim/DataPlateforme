from pathlib import Path
import duckdb

# Racine du projet
ROOT = Path(__file__).resolve().parent.parent

# Base de développement
DB_PATH = ROOT / "data" / "dev.duckdb"

# Fichiers CSV fournis par la personne 1
FILES = {
    "eco2mix_national_cons_def": "eco2mix_cons_def_sample.csv",
    "eco2mix_national_tr": "eco2mix_tr_sample.csv",
    "meteo_horaire": "meteo_sample.csv",
}

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

with duckdb.connect(str(DB_PATH)) as con:

    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    for table, filename in FILES.items():

        csv_path = ROOT / "tests" / "fixtures" / filename

        if not csv_path.exists():
            raise FileNotFoundError(csv_path)

        con.execute(
            f"""
            CREATE OR REPLACE TABLE raw.{table} AS
            SELECT *
            FROM read_csv(
                ?,
                header=true
            )
            """,
            [str(csv_path)],
        )

        count = con.execute(
            f"SELECT COUNT(*) FROM raw.{table}"
        ).fetchone()[0]

        print(f"{table}: {count} lignes")

print("Chargement des échantillons terminé !")
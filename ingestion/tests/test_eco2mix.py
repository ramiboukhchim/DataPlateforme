"""Tests du pipeline eCO2mix, sans réseau (l'API est remplacée par de fausses données).

Lancer depuis la racine du dépôt :  python -m pytest ingestion/tests -v
"""
from datetime import date, datetime, timedelta

import duckdb
import pytest

from ingestion.pipelines import eco2mix


def fake_rows(win_start, win_end, nature="Données définitives", conso=1000, extra=None):
    """Un enregistrement par quart d'heure ; mesure seulement à :00 et :30 (comme eCO2mix)."""
    rows, t = [], datetime.combine(win_start, datetime.min.time())
    end = datetime.combine(win_end, datetime.min.time())
    while t < end:
        has_measure = t.minute in (0, 30)
        row = {
            "perimetre": "France",
            "nature": nature,
            "date_heure": t.strftime("%Y-%m-%dT%H:%M:00+01:00"),
            "consommation": conso if has_measure else None,
            "prevision_j1": 900,
        }
        if extra:
            row.update(extra)
        rows.append(row)
        t += timedelta(minutes=15)
    return rows


def count(db, table):
    con = duckdb.connect(str(db), read_only=True)
    try:
        return con.execute(f"select count(*) from raw.{table}").fetchone()[0]
    finally:
        con.close()


def distinct_keys(db, table):
    con = duckdb.connect(str(db), read_only=True)
    try:
        return con.execute(
            f"select count(*) from (select distinct date_heure, perimetre from raw.{table})"
        ).fetchone()[0]
    finally:
        con.close()


@pytest.fixture
def env(tmp_path, monkeypatch):
    db = tmp_path / "wh.duckdb"
    kw = {"db_path": str(db), "pipelines_dir": str(tmp_path / "dlt")}
    return db, kw, monkeypatch


def test_month_windows_decoupe_par_mois():
    w = list(eco2mix.month_windows(date(2025, 1, 15), date(2025, 3, 10)))
    assert w == [
        (date(2025, 1, 15), date(2025, 2, 1)),
        (date(2025, 2, 1), date(2025, 3, 1)),
        (date(2025, 3, 1), date(2025, 3, 10)),
    ]


def test_idempotence_relancer_ne_double_pas(env):
    db, kw, mp = env
    mp.setattr(eco2mix, "fetch_export", lambda d, s, e: fake_rows(s, e))
    eco2mix.run(["cons-def"], date(2025, 1, 1), date(2025, 1, 4), **kw)
    n1 = count(db, "eco2mix_national_cons_def")
    eco2mix.run(["cons-def"], date(2025, 1, 1), date(2025, 1, 4), **kw)
    n2 = count(db, "eco2mix_national_cons_def")
    assert n1 == 3 * 96          # 3 jours au quart d'heure
    assert n2 == n1              # aucun doublon
    assert distinct_keys(db, "eco2mix_national_cons_def") == n2


def test_merge_met_a_jour_une_ligne_qui_change(env):
    db, kw, mp = env
    mp.setattr(eco2mix, "fetch_export", lambda d, s, e: fake_rows(s, e, nature="Données temps réel", conso=None))
    eco2mix.run(["tr"], date(2025, 1, 1), date(2025, 1, 2), **kw)
    mp.setattr(eco2mix, "fetch_export", lambda d, s, e: fake_rows(s, e, nature="Données consolidées", conso=5000))
    eco2mix.run(["tr"], date(2025, 1, 1), date(2025, 1, 2), **kw)
    con = duckdb.connect(str(db), read_only=True)
    n, nat, conso = con.execute(
        "select count(*), max(nature), max(consommation) from raw.eco2mix_national_tr"
    ).fetchone()
    con.close()
    assert n == 96
    assert nat == "Données consolidées"
    assert conso == 5000


def test_evolution_de_schema_nouvelle_colonne(env):
    db, kw, mp = env
    mp.setattr(eco2mix, "fetch_export", lambda d, s, e: fake_rows(s, e))
    eco2mix.run(["tr"], date(2025, 1, 1), date(2025, 1, 2), **kw)
    mp.setattr(eco2mix, "fetch_export", lambda d, s, e: fake_rows(s, e, extra={"eolien_terrestre": 7}))
    eco2mix.run(["tr"], date(2025, 1, 1), date(2025, 1, 2), **kw)
    con = duckdb.connect(str(db), read_only=True)
    cols = [r[0] for r in con.execute(
        "select column_name from information_schema.columns "
        "where table_schema='raw' and table_name='eco2mix_national_tr'").fetchall()]
    con.close()
    assert "eolien_terrestre" in cols
    assert count(db, "eco2mix_national_tr") == 96

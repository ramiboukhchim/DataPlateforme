"""Tests du pipeline météo, sans réseau (l'API est remplacée par de fausses données).

Lancer depuis la racine du dépôt :  python -m pytest ingestion/tests -v
"""
from datetime import date, datetime, timedelta

import duckdb
import pytest

from ingestion.pipelines import meteo


def fake_hours(lat, lon, win_start, win_end, temp=5.0, rad=0.0):
    rows, t = [], datetime.combine(win_start, datetime.min.time())
    end = datetime.combine(win_end, datetime.min.time())
    while t < end:
        rows.append({
            "time": t.strftime("%Y-%m-%dT%H:%M"),
            "latitude": lat,
            "longitude": lon,
            "temperature_2m": temp,
            "shortwave_radiation": rad,
        })
        t += timedelta(hours=1)
    return rows


def query(db, sql):
    con = duckdb.connect(str(db), read_only=True)
    try:
        return con.execute(sql).fetchone()
    finally:
        con.close()


@pytest.fixture
def env(tmp_path, monkeypatch):
    db = tmp_path / "wh.duckdb"
    return db, {"db_path": str(db), "pipelines_dir": str(tmp_path / "dlt")}, monkeypatch


def test_year_windows_decoupe_par_annee():
    assert list(meteo.year_windows(date(2024, 6, 1), date(2026, 2, 1))) == [
        (date(2024, 6, 1), date(2025, 1, 1)),
        (date(2025, 1, 1), date(2026, 1, 1)),
        (date(2026, 1, 1), date(2026, 2, 1)),
    ]


def test_idempotence_relancer_ne_double_pas(env):
    db, kw, mp = env
    mp.setattr(meteo, "fetch_hourly", fake_hours)
    meteo.run(date(2025, 1, 1), date(2025, 1, 4), **kw)
    n1 = query(db, "select count(*) from raw.meteo_horaire")[0]
    meteo.run(date(2025, 1, 1), date(2025, 1, 4), **kw)
    n2 = query(db, "select count(*) from raw.meteo_horaire")[0]
    assert n1 == 3 * 24
    assert n2 == n1
    assert query(db, "select count(distinct time) from raw.meteo_horaire")[0] == n2


def test_merge_remplace_une_valeur_nulle_par_la_mesure(env):
    """L'archive peut renvoyer null pour les derniers jours, complétés plus tard."""
    db, kw, mp = env
    mp.setattr(meteo, "fetch_hourly", lambda a, b, s, e: fake_hours(a, b, s, e, temp=None, rad=None))
    meteo.run(date(2025, 1, 1), date(2025, 1, 2), **kw)
    mp.setattr(meteo, "fetch_hourly", lambda a, b, s, e: fake_hours(a, b, s, e, temp=7.5, rad=120.0))
    meteo.run(date(2025, 1, 1), date(2025, 1, 2), **kw)
    n, t, r = query(db, "select count(*), max(temperature_2m), max(shortwave_radiation) from raw.meteo_horaire")
    assert (n, t, r) == (24, 7.5, 120.0)


def test_fenetre_multi_annees_charge_tout(env):
    db, kw, mp = env
    mp.setattr(meteo, "fetch_hourly", fake_hours)
    meteo.run(date(2024, 12, 31), date(2025, 1, 2), **kw)   # a cheval sur deux années
    assert query(db, "select count(*) from raw.meteo_horaire")[0] == 2 * 24   # 31/12 et 01/01

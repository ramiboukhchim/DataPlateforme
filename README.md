# Plateforme DataOps - Énergie (eCO2mix + Open-Meteo)

Plateforme de données de bout en bout : ingestion, transformation, qualité,
orchestration, observabilité.

## Démarrage rapide
```
git clone <url-du-depot>
cd DataPlateforme
copy .env.example .env      # puis remplir les valeurs
docker compose up -d
```

## Organisation
| Dossier | Contenu | Responsable initial |
|---|---|---|
| `ingestion/`, `orchestration/`, `infra/` | dlt, Prefect, Docker, monitoring | Personne A |
| `dbt/`, `tests/`, `dashboard/`, `.github/` | dbt, qualité, CI, tableau de bord | Personne B |
| `contracts/`, `docs/` | contrats de données, décisions | Les deux |

## Documentation
- Questions métier : `docs/questions_metier.md`
- Décisions d'architecture : `docs/decisions/`

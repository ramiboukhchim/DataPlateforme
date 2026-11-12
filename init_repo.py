"""Crée la structure du dépôt DataOps (sujet Énergie).

Usage (depuis le dossier du dépôt, ex. DataPlateforme) :
    python init_repo.py            # crée dans le dossier courant
    python init_repo.py mon_dossier

Le script n'écrase jamais un fichier existant.
"""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

# Dossiers vides conservés par Git grâce à un .gitkeep
DIRS = [
    "docs/decisions",
    "contracts",
    "ingestion/pipelines",
    "ingestion/tests",
    "orchestration",
    "infra/monitoring",
    "dbt/models/staging",
    "dbt/models/intermediate",
    "dbt/models/marts",
    "dbt/tests",
    "dbt/macros",
    "dbt/seeds",
    "tests",
    "dashboard",
    ".github/workflows",
    "data",
]

FILES = {}

FILES[".gitignore"] = """\
# Secrets : ne JAMAIS commiter
.env
*.pem
*.key

# Python
__pycache__/
*.pyc
.venv/
venv/

# dbt
dbt/target/
dbt/dbt_packages/
dbt/logs/

# Données et bases locales (volumineuses, reproductibles)
data/*
!data/.gitkeep
*.duckdb
*.duckdb.wal
*.parquet

# Outils
.pytest_cache/
.ruff_cache/
.DS_Store
"""

FILES[".env.example"] = """\
# Copier ce fichier en .env puis remplacer les valeurs. Ne commitez jamais .env.
MINIO_ROOT_USER=changeme_user
MINIO_ROOT_PASSWORD=changeme_password_min8
MINIO_BUCKET=raw

# Entrepôt local
DUCKDB_PATH=data/warehouse.duckdb

# Ville de référence pour la météo (décision : une seule ville au départ)
METEO_LATITUDE=48.8566
METEO_LONGITUDE=2.3522
"""

FILES["docker-compose.yml"] = """\
# Socle minimal : MinIO (stockage objet compatible S3).
# TODO : épingler une version précise de l'image (reproductibilité exigée par le sujet).
services:
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"   # API S3
      - "9001:9001"   # console web
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data

volumes:
  minio_data:
"""

FILES["README.md"] = """\
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
"""

FILES["docs/questions_metier.md"] = """\
# Questions métier

1. **Q1** - Quelle est la part de production renouvelable (éolien, solaire,
   hydraulique, bioénergies) dans la production totale, par heure de la journée
   et par mois ? *(eCO2mix)*
2. **Q2** - La consommation d'électricité suit-elle la température ? Quel écart
   de consommation par degré en moins ? *(eCO2mix + Open-Meteo)*
3. **Q3** - La production solaire dépend-elle de l'ensoleillement, et à quelles
   heures dépasse-t-elle 5 GW ? *(eCO2mix + Open-Meteo)*
"""

FILES["docs/decisions/001-sources-eco2mix.md"] = """\
# ADR-001 : Deux jeux eCO2mix complémentaires

**Statut** : accepté

## Contexte
L'API ODRE (Explore v2.1) expose deux jeux nationaux :
- `eco2mix-national-cons-def` : 514 272 lignes, jusqu'au 31/08/2026
  (490 944 « définitives » 2012-2025, 23 328 « consolidées » 2026).
- `eco2mix-national-tr` : fenêtre glissante (~74 jours, septembre 2026 à aujourd'hui),
  nature « Données temps réel ».

## Décision
Ingérer les deux. Une même heure peut exister dans les deux jeux : la version
retenue suit la priorité définitif > consolidé > temps réel (modèle `int_`).
Les schémas diffèrent (`eolien_terrestre`, `eolien_offshore`, `stockage_batterie`,
`destockage_batterie` n'existent que dans `tr`) : harmonisation au staging.

## Conséquences
- Deux contrats de données distincts.
- Pour l'historique, préférer l'export plutôt que des milliers d'appels (quota d'API
  annoncé par ODRE, à vérifier).
"""

FILES["docs/decisions/002-fuseau-horaire-utc.md"] = """\
# ADR-002 : Tout convertir en UTC au staging

**Statut** : accepté

## Contexte
eCO2mix renvoie `2026-11-13T23:45:00+01:00` (décalage variable selon l'heure d'été),
Open-Meteo renvoie `2026-10-01T00:00` sans décalage, dans le fuseau demandé.
Les jours de changement d'heure comptent 23 ou 25 heures.

## Décision
Convertir tous les horodatages en UTC dès la couche staging. La jointure
énergie/météo se fait uniquement sur l'heure UTC.

## Conséquences
Les affichages en heure locale se calculent à la fin, dans le tableau de bord.
"""

FILES["docs/decisions/003-lignes-sans-mesure.md"] = """\
# ADR-003 : Traitement des créneaux sans mesure

**Statut** : à confirmer

## Contexte
Environ 50 % des lignes (257 135 sur 514 272 dans `cons-def`) ont une
consommation renseignée. Les autres ne contiennent que des prévisions
(`prevision_j`, `prevision_j1`).

## Décision proposée
Au staging, conserver ces lignes mais les marquer (`has_measure = false`).
Les marts de mesure ne gardent que `has_measure = true`. Les lignes de mesure
avec valeurs incohérentes vont en quarantaine.

## À confirmer
Vérifier que le motif « mesure toutes les 30 min » est stable sur toute la période.
"""

FILES["docs/runbook.md"] = "# Runbook\n\nÀ compléter : symptôme, diagnostic, correction, vérification.\n"
FILES["contracts/README.md"] = "# Contrats de données\n\nUn fichier YAML par source (voir ADR-001).\n"
FILES["dbt/README.md"] = "# Projet dbt\n\nÀ initialiser par la personne B (`dbt init`).\n"
FILES["ingestion/README.md"] = "# Ingestion (dlt)\n\nÀ implémenter par la personne A.\n"


def write_if_absent(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"  existe déjà : {path.relative_to(ROOT)}")
        return
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"  créé        : {path.relative_to(ROOT)}")


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    print(f"Dépôt : {ROOT.resolve()}")
    for d in DIRS:
        write_if_absent(ROOT / d / ".gitkeep", "")
    for name, content in FILES.items():
        write_if_absent(ROOT / name, content)
    print("\nTerminé. Étape suivante : git add . puis git commit.")

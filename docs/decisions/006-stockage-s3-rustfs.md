# ADR-006 : RustFS à la place de MinIO

Statut : accepté

## Contexte
L'image minio/minio a été retirée de Docker Hub (erreur "pull access denied").
Le sujet demande un stockage objet compatible S3.

## Décision
Utiliser RustFS 1.0.0 (licence Apache 2.0, API S3, console web), avec la version
épinglée dans docker-compose.yml.

## Alternatives écartées
- Garage : pas de console web.
- Image Chainguard de MinIO : un seul tag, pas de version épinglable.

## Conséquences
- Variables d'environnement renommées en S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET.
- RustFS peut consommer environ 1 Go de mémoire : à surveiller avec Grafana.
- Compatibilité avec le niveau avancé (Iceberg) à vérifier.
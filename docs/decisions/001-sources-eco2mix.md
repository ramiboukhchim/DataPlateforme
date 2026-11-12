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

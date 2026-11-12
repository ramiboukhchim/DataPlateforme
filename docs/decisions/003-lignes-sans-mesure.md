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

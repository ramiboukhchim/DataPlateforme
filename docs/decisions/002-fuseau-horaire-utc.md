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

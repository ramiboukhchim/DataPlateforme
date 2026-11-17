-- Dimension calendrier : une ligne par heure UTC

with heures as (

    select distinct
        date_heure_utc

    from {{ ref('int_energie_meteo_horaire') }}

),

calendrier as (

    select
        date_heure_utc as date_heure_id,

        cast(date_heure_utc as date) as date_jour,

        year(date_heure_utc) as annee,

        month(date_heure_utc) as mois,

        day(date_heure_utc) as jour,

        hour(date_heure_utc) as heure,

        dayofweek(date_heure_utc) as jour_semaine,

        quarter(date_heure_utc) as trimestre

    from heures

)

select *
from calendrier
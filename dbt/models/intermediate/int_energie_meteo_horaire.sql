-- Agregation horaire de l'energie
-- Jointure avec la meteo sur l'heure UTC

with energie as (

    select *
    from {{ ref('int_eco2mix_unifie') }}

),

meteo as (

    select *
    from {{ ref('stg_meteo') }}

),

energie_horaire as (

    select
        date_trunc('hour', date_heure_utc)
            as date_heure_utc,

        perimetre,

        avg(consommation_mw) as consommation_mw,

        avg(eolien_mw) as eolien_mw,
        avg(solaire_mw) as solaire_mw,
        avg(hydraulique_mw) as hydraulique_mw,
        avg(bioenergies_mw) as bioenergies_mw,
        avg(nucleaire_mw) as nucleaire_mw,
        avg(gaz_mw) as gaz_mw,
        avg(charbon_mw) as charbon_mw,
        avg(fioul_mw) as fioul_mw,

        count(*) as nb_observations,
        count(consommation_mw) as nb_mesures

    from energie

    group by
        date_trunc('hour', date_heure_utc),
        perimetre

),

resultat as (

    select
        e.*,

        m.temperature_c,
        m.rayonnement_w_m2

    from energie_horaire e

    left join meteo m
        on e.date_heure_utc = m.date_heure_utc

)

select *
from resultat
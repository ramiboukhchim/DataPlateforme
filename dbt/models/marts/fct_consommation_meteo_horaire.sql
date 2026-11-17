-- Table de faits consommation et meteo
-- Une ligne par heure UTC et perimetre

with source_data as (

    select *
    from {{ ref('int_energie_meteo_horaire') }}

),

final as (

    select
        date_heure_utc as date_heure_id,

        cast(perimetre as varchar) as perimetre,

        cast(consommation_mw as double)
            as consommation_mw,

        cast(temperature_c as double)
            as temperature_c,

        cast(rayonnement_w_m2 as double)
            as rayonnement_w_m2,

        cast(solaire_mw as double)
            as solaire_mw,

        cast(nb_observations as integer)
            as nb_observations,

        cast(nb_mesures as integer)
            as nb_mesures

    from source_data

)

select *
from final
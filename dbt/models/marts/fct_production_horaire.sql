{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key=[
            'date_heure_id',
            'perimetre',
            'filiere_id'
        ]
    )
}}

-- Une ligne par heure, perimetre et filiere

with energie as (

    select *
    from {{ ref('int_energie_meteo_horaire') }}

    {% if is_incremental() %}

    -- Recalculer les 2 derniers jours
    -- pour prendre en compte les corrections recentes
    where date_heure_utc >= (
        select coalesce(
            max(date_heure_id) - interval '2 days',
            timestamp '1900-01-01'
        )
        from {{ this }}
    )

    {% endif %}

),

production_longue as (

    select
        e.date_heure_utc as date_heure_id,
        e.perimetre,
        f.filiere_id,
        cast(f.production_mw as double) as production_mw

    from energie e

    cross join lateral (
        values
            ('eolien', e.eolien_mw),
            ('solaire', e.solaire_mw),
            ('hydraulique', e.hydraulique_mw),
            ('bioenergies', e.bioenergies_mw),
            ('nucleaire', e.nucleaire_mw),
            ('gaz', e.gaz_mw),
            ('charbon', e.charbon_mw),
            ('fioul', e.fioul_mw)
    ) as f(filiere_id, production_mw)

)

select
    date_heure_id,
    perimetre,
    filiere_id,
    production_mw

from production_longue

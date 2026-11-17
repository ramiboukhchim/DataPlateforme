-- Staging des donnees meteorologiques
-- Hypothese : les heures de la source sont en UTC

with source_data as (

    select *
    from {{ source('raw', 'meteo_horaire') }}

),

cleaned as (

    select
        cast(time as timestamp) as date_heure_utc,

        cast(temperature_2m as double) as temperature_c,

        cast(shortwave_radiation as double) as rayonnement_w_m2

    from source_data

)

select *
from cleaned
-- Staging des donnees temps reel eCO2mix

with source_data as (

    select *
    from {{ source('raw', 'eco2mix_national_tr') }}

),

cleaned as (

    select
        -- Heure UTC
        {{ to_utc('date_heure') }} as date_heure_utc,

        -- Consommation
        cast(consommation as bigint) as consommation_mw,
        consommation is not null as has_measure,

        -- Production par filiere
        cast(eolien as bigint) as eolien_mw,
        cast(solaire as bigint) as solaire_mw,
        cast(hydraulique as bigint) as hydraulique_mw,
        cast(bioenergies as bigint) as bioenergies_mw,
        cast(nucleaire as bigint) as nucleaire_mw,
        cast(gaz as bigint) as gaz_mw,
        cast(charbon as bigint) as charbon_mw,
        cast(fioul as bigint) as fioul_mw,

        -- Colonnes supplementaires temps reel
        cast(eolien_terrestre as bigint) as eolien_terrestre_mw,
        cast(eolien_offshore as bigint) as eolien_offshore_mw,
        cast(stockage_batterie as bigint) as stockage_batterie_mw,
        cast(destockage_batterie as bigint) as destockage_batterie_mw,

        -- Informations complementaires
        cast(pompage as bigint) as pompage_mw,
        cast(prevision_j as bigint) as prevision_j_mw,
        cast(prevision_j1 as bigint) as prevision_j1_mw,

        cast(nature as varchar) as nature,
        cast(perimetre as varchar) as perimetre

    from source_data

)

select *
from cleaned
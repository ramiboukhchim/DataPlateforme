-- Reunir les donnees historiques et temps reel
-- Priorite : definitives > consolidees > temps reel

with toutes_les_donnees as (

    select *
    from {{ ref('stg_eco2mix_cons_def') }}

    union all

    select *
    from {{ ref('stg_eco2mix_tr') }}

),

avec_priorite as (

    select
        *,

        case
            when nature = 'Données définitives' then 1
            when nature = 'Données consolidées' then 2
            when nature = 'Données temps réel' then 3
            else 4
        end as priorite

    from toutes_les_donnees

),

classement as (

    select
        *,

        row_number() over (
            partition by date_heure_utc, perimetre
            order by priorite asc,
                     has_measure desc
        ) as rang

    from avec_priorite

)

select * exclude (priorite, rang)
from classement
where rang = 1
-- Dimension des filieres de production

with filieres as (

    select *
    from {{ ref('filieres') }}

)

select
    cast(filiere_id as varchar) as filiere_id,
    cast(nom_filiere as varchar) as nom_filiere,
    cast(est_renouvelable as boolean) as est_renouvelable

from filieres
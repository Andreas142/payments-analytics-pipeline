-- Silver: one clean row per product, with English category names.
-- Joins the Portuguese category to its English translation, and gives
-- products with a missing category an explicit 'unknown' rather than null,
-- so they still appear in category-level metrics downstream.

with products as (
    select * from {{ ref('stg_products') }}
),

translation as (
    select * from {{ ref('stg_category_translation') }}
)

select
    p.product_id,
    coalesce(t.category_name_en, p.category_name_pt, 'unknown') as category,
    p.weight_g,
    p.length_cm,
    p.height_cm,
    p.width_cm
from products as p
left join translation as t
    on p.category_name_pt = t.category_name_pt

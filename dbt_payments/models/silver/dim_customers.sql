-- Silver: one row per real customer.
-- Olist quirk: customer_id is order-scoped (new id per order), while
-- customer_unique_id identifies the actual person across orders. We model at
-- the person grain and keep location from their most recent record.

with customers as (
    select * from {{ ref('stg_customers') }}
),

ranked as (
    select
        customer_unique_id,
        customer_id,
        zip_code_prefix,
        city,
        state,
        row_number() over (
            partition by customer_unique_id
            order by customer_id
        ) as rn
    from customers
)

select
    customer_unique_id,
    zip_code_prefix,
    city,
    state
from ranked
where rn = 1

-- One row per customer (order-scoped in Olist: a new customer_id per order,
-- with customer_unique_id linking a real person across orders).
select
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix   as zip_code_prefix,
    customer_city              as city,
    customer_state             as state
from {{ source('olist', 'olist_customers_dataset') }}

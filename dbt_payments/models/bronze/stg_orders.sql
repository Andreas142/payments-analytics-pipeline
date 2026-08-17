-- Bronze staging model for orders.
-- One row per order. Light-touch: select from source, standardise names/types.
-- No business logic here (that belongs in silver).

select
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp   as ordered_at,
    order_approved_at          as approved_at,
    order_delivered_carrier_date   as delivered_to_carrier_at,
    order_delivered_customer_date  as delivered_to_customer_at,
    order_estimated_delivery_date  as estimated_delivery_at

from {{ source('olist', 'olist_orders_dataset') }}

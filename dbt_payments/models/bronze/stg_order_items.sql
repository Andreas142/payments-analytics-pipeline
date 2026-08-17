-- One row per item line within an order (an order can have several items).
select
    order_id,
    order_item_id              as item_number,
    product_id,
    seller_id,
    shipping_limit_date        as shipping_limit_at,
    price,
    freight_value              as freight
from {{ source('olist', 'olist_order_items_dataset') }}

-- Intermediate: total value of each order from its item lines.
-- Order value = sum of item price + freight across all items in the order.

with items as (
    select * from {{ ref('stg_order_items') }}
)

select
    order_id,
    count(*)                          as item_count,
    round(sum(price), 2)              as items_price,
    round(sum(freight), 2)            as items_freight,
    round(sum(price + freight), 2)    as order_value
from items
group by order_id

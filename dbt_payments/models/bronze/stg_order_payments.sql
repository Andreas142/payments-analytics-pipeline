-- One row per payment on an order (an order can be split across methods).
select
    order_id,
    payment_sequential         as payment_number,
    payment_type,
    payment_installments       as installments,
    payment_value
from {{ source('olist', 'olist_order_payments_dataset') }}

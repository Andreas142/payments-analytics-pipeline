-- Intermediate: total actually paid per order.
-- An order can be split across multiple payment methods/rows, so we sum them
-- to one row per order. Also capture method count + whether a voucher was used,
-- since those explain many reconciliation differences later.

with payments as (
    select * from {{ ref('stg_order_payments') }}
)

select
    order_id,
    count(*)                                        as payment_row_count,
    count(distinct payment_type)                    as distinct_payment_types,
    max(case when payment_type = 'voucher' then 1 else 0 end) = 1 as used_voucher,
    round(sum(payment_value), 2)                    as total_paid
from payments
group by order_id

-- Intermediate: total paid per order, plus the dominant payment method.
-- An order can split across methods/rows, so we sum to one row per order and
-- also flag the method that accounts for the largest share of the payment.

with payments as (
    select * from {{ ref('stg_order_payments') }}
),

order_totals as (
    select
        order_id,
        count(*)                                             as payment_row_count,
        count(distinct payment_type)                         as distinct_payment_types,
        max(case when payment_type = 'voucher' then 1 else 0 end) = 1 as used_voucher,
        round(sum(payment_value), 2)                         as total_paid
    from payments
    group by order_id
),

dominant_method as (
    -- Rank each order's payment types by total value; keep the top one.
    select order_id, payment_type as dominant_payment_type
    from (
        select
            order_id,
            payment_type,
            row_number() over (
                partition by order_id
                order by sum(payment_value) desc, payment_type
            ) as rn
        from payments
        group by order_id, payment_type
    ) ranked
    where rn = 1
)

select
    t.*,
    d.dominant_payment_type
from order_totals as t
left join dominant_method as d on t.order_id = d.order_id

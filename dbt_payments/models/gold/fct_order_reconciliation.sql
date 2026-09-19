-- Gold: order-level reconciliation of payments vs order value. One row per order.
-- Full outer join keeps orders present on only one side. Each order is classified
-- so breaks are explained, not just flagged. Now also carries the order month and
-- dominant payment method for reporting.

with orders as (
    select order_id, order_status, ordered_at from {{ ref('stg_orders') }}
),

paid as (
    select * from {{ ref('int_order_payments') }}
),

value as (
    select * from {{ ref('int_order_values') }}
),

joined as (
    select
        coalesce(p.order_id, v.order_id)          as order_id,
        o.order_status,
        o.ordered_at,
        strftime(o.ordered_at, '%Y-%m')           as order_month,
        v.order_value,
        v.item_count,
        p.total_paid,
        p.payment_row_count,
        p.used_voucher,
        p.dominant_payment_type,
        round(coalesce(p.total_paid, 0)
              - coalesce(v.order_value, 0), 2)     as paid_minus_value
    from paid as p
    full outer join value as v on p.order_id = v.order_id
    left join orders as o
        on coalesce(p.order_id, v.order_id) = o.order_id
)

select
    *,
    case
        when total_paid is null                        then 'missing_payment'
        when order_value is null                       then 'missing_items'
        when abs(paid_minus_value) <= 0.01             then 'reconciled'
        when used_voucher and paid_minus_value < 0     then 'voucher_reduced'
        when paid_minus_value > 0                       then 'overpaid_or_interest'
        else 'underpaid'
    end as recon_status
from joined

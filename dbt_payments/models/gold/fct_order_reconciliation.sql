-- Gold: order-level reconciliation of payments vs order value.
-- One row per order (full outer join so we keep orders that exist on only one
-- side). Computes the difference and classifies it, so breaks are explained,
-- not just flagged. This is the domain showpiece.

with orders as (
    select order_id, order_status from {{ ref('stg_orders') }}
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
        v.order_value,
        v.item_count,
        p.total_paid,
        p.payment_row_count,
        p.used_voucher,
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

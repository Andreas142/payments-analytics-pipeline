-- One row per seller.
select
    seller_id,
    seller_zip_code_prefix     as zip_code_prefix,
    seller_city                as city,
    seller_state               as state
from {{ source('olist', 'olist_sellers_dataset') }}

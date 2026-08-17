-- One row per review. Comment fields are often null (ratings without text).
select
    review_id,
    order_id,
    review_score,
    review_comment_title       as comment_title,
    review_comment_message     as comment_message,
    review_creation_date       as created_at,
    review_answer_timestamp    as answered_at
from {{ source('olist', 'olist_order_reviews_dataset') }}

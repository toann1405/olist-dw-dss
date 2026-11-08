-- operator: dice
-- question: For Norte and Nordeste customers, 2018 Q1-Q2, bulky goods, what are late and bad-review rates by seller state?
-- requirement: R25
-- tables: gold.fact_order, gold.fact_order_item, gold.dim_date, gold.dim_product, gold.dim_seller

-- Run after USE CATALOG olist_catalog.
-- Drill-across from DESIGN section 3.6. Review rate is the seller measure, not the marketplace KPI.

WITH region_orders AS (
  SELECT o.order_id
  FROM gold.fact_order AS o
  INNER JOIN gold.dim_date AS d
    ON o.purchase_date_key = d.date_key
  WHERE o.customer_region_name IN ('Norte', 'Nordeste')
    AND d.year = 2018
    AND d.quarter IN (1, 2)
),
bulky_sellers AS (
  SELECT DISTINCT
    i.order_id,
    i.seller_key
  FROM gold.fact_order_item AS i
  INNER JOIN region_orders AS r
    ON i.order_id = r.order_id
  INNER JOIN gold.dim_product AS p
    ON i.product_key = p.product_key
  WHERE p.size_band = 'bulky'
    AND i.seller_key <> -1
)
SELECT
  s.state_code,
  COUNT(DISTINCT CASE WHEN o.late_flag = 1 THEN b.order_id END) AS late_orders,
  COUNT(DISTINCT CASE WHEN o.late_flag IS NOT NULL THEN b.order_id END) AS late_eligible_orders,
  CASE
    WHEN COUNT(DISTINCT CASE WHEN o.late_flag IS NOT NULL THEN b.order_id END) > 0
      THEN COUNT(DISTINCT CASE WHEN o.late_flag = 1 THEN b.order_id END)
        / COUNT(DISTINCT CASE WHEN o.late_flag IS NOT NULL THEN b.order_id END)
  END AS late_delivery_rate,
  COUNT(DISTINCT CASE
    WHEN o.n_sellers = 1
      AND o.shared_review_type IN ('none', 'same_seller')
      AND o.negative_review_flag = 1
      THEN b.order_id
  END) AS negative_review_orders,
  COUNT(DISTINCT CASE
    WHEN o.n_sellers = 1
      AND o.shared_review_type IN ('none', 'same_seller')
      AND o.negative_review_flag IS NOT NULL
      THEN b.order_id
  END) AS review_eligible_orders,
  CASE
    WHEN COUNT(DISTINCT CASE
      WHEN o.n_sellers = 1
        AND o.shared_review_type IN ('none', 'same_seller')
        AND o.negative_review_flag IS NOT NULL
        THEN b.order_id
    END) > 0
      THEN COUNT(DISTINCT CASE
        WHEN o.n_sellers = 1
          AND o.shared_review_type IN ('none', 'same_seller')
          AND o.negative_review_flag = 1
          THEN b.order_id
      END)
        / COUNT(DISTINCT CASE
          WHEN o.n_sellers = 1
            AND o.shared_review_type IN ('none', 'same_seller')
            AND o.negative_review_flag IS NOT NULL
            THEN b.order_id
        END)
  END AS seller_negative_review_rate
FROM bulky_sellers AS b
INNER JOIN gold.fact_order AS o
  ON b.order_id = o.order_id
INNER JOIN gold.dim_seller AS s
  ON b.seller_key = s.seller_key
GROUP BY s.state_code
ORDER BY s.state_code;

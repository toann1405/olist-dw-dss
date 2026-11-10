-- Feature view for the DSS. Gold tables only.
-- The DSS notebook wraps this SELECT in
-- CREATE OR REPLACE VIEW catalog.dss.v_seller_features.
-- Placeholders {catalog} and {gold} are filled from job widgets.

WITH item_month AS (
  SELECT
    i.seller_key,
    d.month_key,
    p.category_group,
    i.distance_km
  FROM {catalog}.{gold}.fact_order_item AS i
  INNER JOIN {catalog}.{gold}.dim_date AS d
    ON i.purchase_date_key = d.date_key
  INNER JOIN {catalog}.{gold}.dim_product AS p
    ON i.product_key = p.product_key
  WHERE i.seller_key <> -1
    AND d.date_key <> -1
    AND p.product_key <> -1
),
distance_by_month AS (
  SELECT
    seller_key,
    month_key,
    AVG(distance_km) AS avg_distance_km
  FROM item_month
  WHERE distance_km IS NOT NULL
  GROUP BY seller_key, month_key
),
category_counts AS (
  SELECT
    seller_key,
    month_key,
    category_group,
    COUNT(*) AS n_items
  FROM item_month
  GROUP BY seller_key, month_key, category_group
),
category_ranked AS (
  SELECT
    seller_key,
    month_key,
    category_group,
    ROW_NUMBER() OVER (
      PARTITION BY seller_key, month_key
      ORDER BY n_items DESC, category_group ASC
    ) AS rn
  FROM category_counts
)
SELECT
  f.seller_key,
  f.seller_id,
  f.month_key,
  f.year_month,
  f.n_orders_valid,
  f.n_items_valid,
  f.gmv,
  f.late_ship_rate,
  f.avg_review,
  f.bad_experience_count,
  f.bad_experience_eligible,
  s.region_name,
  s.has_closed_deal,
  s.won_date,
  AVG(f.late_ship_rate) OVER (
    PARTITION BY f.seller_key
    ORDER BY f.month_key
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
  ) AS late_ship_rate_3m,
  dist.avg_distance_km,
  cat.category_group,
  CASE
    WHEN s.won_date IS NULL THEN NULL
    ELSE DATEDIFF(MAKE_DATE(m.year, m.month, 1), s.won_date)
  END AS seller_age_days
FROM {catalog}.{gold}.fact_seller_monthly AS f
INNER JOIN {catalog}.{gold}.dim_seller AS s
  ON f.seller_key = s.seller_key
INNER JOIN {catalog}.{gold}.dim_month AS m
  ON f.month_key = m.month_key
LEFT JOIN distance_by_month AS dist
  ON f.seller_key = dist.seller_key
 AND f.month_key = dist.month_key
LEFT JOIN category_ranked AS cat
  ON f.seller_key = cat.seller_key
 AND f.month_key = cat.month_key
 AND cat.rn = 1
WHERE f.seller_key <> -1
  AND s.seller_key <> -1
  AND m.month_key <> -1

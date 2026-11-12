-- requirement: R09
-- tables: gold.fact_order_item, gold.fact_order, gold.dim_order_status, gold.dim_product, gold.dim_seller, gold.dim_date
-- rates from numerator and denominator

WITH items AS (
  SELECT
    p.category_group,
    i.order_id,
    i.price
  FROM {catalog}.{gold}.fact_order_item AS i
  INNER JOIN {catalog}.{gold}.fact_order AS o
    ON i.order_id = o.order_id
  INNER JOIN {catalog}.{gold}.dim_order_status AS st
    ON o.order_status_key = st.order_status_key
  INNER JOIN {catalog}.{gold}.dim_product AS p
    ON i.product_key = p.product_key
  INNER JOIN {catalog}.{gold}.dim_seller AS s
    ON i.seller_key = s.seller_key
  INNER JOIN {catalog}.{gold}.dim_date AS d
    ON i.purchase_date_key = d.date_key
  WHERE i.seller_key <> -1
    AND s.seller_key <> -1
    AND p.product_key <> -1
    AND d.date_key <> -1
    AND (st.order_status IS NULL OR st.order_status NOT IN ('canceled', 'unavailable'))
    AND ({p} IS NULL OR format_string('%04d-%02d', d.year, d.month) >= {p})
    AND ({p} IS NULL OR format_string('%04d-%02d', d.year, d.month) <= {p})
    AND ({p} IS NULL OR s.region_name = {p})
    AND ({p} IS NULL OR s.state_code = {p})
)
SELECT
  category_group,
  SUM(price) AS gmv,
  COUNT(*) AS n_items
FROM items
GROUP BY category_group
ORDER BY gmv DESC
LIMIT 10

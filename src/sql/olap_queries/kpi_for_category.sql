-- requirement: R09
-- tables: gold.fact_order_item, gold.fact_order, gold.dim_order_status, gold.dim_product, gold.dim_seller, gold.dim_date
-- rates from numerator and denominator
-- Used only when a category_group is selected. The unfiltered KPI cards do not use this file.

WITH items AS (
  SELECT
    i.order_id,
    i.price,
    i.seller_ship_late_flag,
    st.order_status
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
    AND ({p} IS NULL OR format_string('%04d-%02d', d.year, d.month) >= {p})
    AND ({p} IS NULL OR format_string('%04d-%02d', d.year, d.month) <= {p})
    AND ({p} IS NULL OR s.region_name = {p})
    AND ({p} IS NULL OR s.state_code = {p})
    AND p.category_group = {p}
)
SELECT
  SUM(
    CASE
      WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
        THEN price
    END
  ) AS gmv,
  COUNT(DISTINCT
    CASE
      WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
        THEN order_id
    END
  ) AS valid_orders,
  SUM(CASE WHEN seller_ship_late_flag = 1 THEN 1 ELSE 0 END) AS late_ship_count,
  SUM(CASE WHEN seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END) AS late_ship_eligible,
  COUNT(DISTINCT CASE WHEN order_status IN ('canceled', 'unavailable') THEN order_id END) AS cancel_orders,
  COUNT(DISTINCT order_id) AS placed_orders
FROM items

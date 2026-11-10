-- operator: slice
-- question: Within one category group, which sellers have the highest late-delivery rate?
-- requirement: R25
-- tables: gold.fact_order_item, gold.dim_product, gold.dim_seller

-- Run after USE CATALOG olist_catalog.
-- category_group is a bound parameter. The 07/11/2026 run used electronics_it_telephony.
-- late_delivery_flag is an order flag copied onto items. Count distinct orders.

WITH orders_in_group AS (
  SELECT DISTINCT
    i.order_id,
    i.seller_key,
    i.late_delivery_flag
  FROM gold.fact_order_item AS i
  INNER JOIN gold.dim_product AS p
    ON i.product_key = p.product_key
  WHERE p.category_group = {p}
    AND i.seller_key <> -1
)
SELECT
  s.seller_id,
  s.seller_key,
  s.state_code,
  COUNT(DISTINCT CASE WHEN g.late_delivery_flag = 1 THEN g.order_id END) AS late_orders,
  COUNT(DISTINCT CASE WHEN g.late_delivery_flag IS NOT NULL THEN g.order_id END) AS eligible_orders,
  CASE
    WHEN COUNT(DISTINCT CASE WHEN g.late_delivery_flag IS NOT NULL THEN g.order_id END) > 0
      THEN COUNT(DISTINCT CASE WHEN g.late_delivery_flag = 1 THEN g.order_id END)
        / COUNT(DISTINCT CASE WHEN g.late_delivery_flag IS NOT NULL THEN g.order_id END)
  END AS late_delivery_rate
FROM orders_in_group AS g
INNER JOIN gold.dim_seller AS s
  ON g.seller_key = s.seller_key
GROUP BY s.seller_id, s.seller_key, s.state_code
ORDER BY late_delivery_rate DESC, eligible_orders DESC;

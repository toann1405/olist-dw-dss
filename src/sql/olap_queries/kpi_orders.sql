-- operator: kpi
-- question: AOV and cancel rate from distinct orders for one purchase year and seller region
-- requirement: R09
-- tables: gold.fact_order_item, gold.fact_order, gold.dim_order_status, gold.dim_seller, gold.dim_date
-- rates from numerator and denominator

WITH touched AS (
  SELECT
    i.order_id,
    i.price,
    st.order_status
  FROM {catalog}.{gold}.fact_order_item AS i
  INNER JOIN {catalog}.{gold}.fact_order AS o
    ON i.order_id = o.order_id
  INNER JOIN {catalog}.{gold}.dim_order_status AS st
    ON o.order_status_key = st.order_status_key
  INNER JOIN {catalog}.{gold}.dim_seller AS s
    ON i.seller_key = s.seller_key
  INNER JOIN {catalog}.{gold}.dim_date AS d
    ON i.purchase_date_key = d.date_key
  WHERE i.seller_key <> -1
    AND s.seller_key <> -1
    AND d.date_key <> -1
    AND ({p} IS NULL OR d.year = {p})
    AND ({p} IS NULL OR s.region_name = {p})
    AND ({p} IS NULL OR s.state_code = {p})
)
SELECT
  SUM(
    CASE
      WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
        THEN price
    END
  ) AS gmv_from_items,
  COUNT(DISTINCT
    CASE
      WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
        THEN order_id
    END
  ) AS valid_orders,
  CASE
    WHEN COUNT(DISTINCT
      CASE
        WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
          THEN order_id
      END
    ) > 0
      THEN SUM(
        CASE
          WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
            THEN price
        END
      ) / COUNT(DISTINCT
        CASE
          WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
            THEN order_id
        END
      )
  END AS aov,
  COUNT(DISTINCT CASE WHEN order_status IN ('canceled', 'unavailable') THEN order_id END) AS cancel_orders,
  COUNT(DISTINCT order_id) AS placed_orders,
  CASE
    WHEN COUNT(DISTINCT order_id) > 0
      THEN COUNT(DISTINCT CASE WHEN order_status IN ('canceled', 'unavailable') THEN order_id END)
        / COUNT(DISTINCT order_id)
  END AS cancel_rate
FROM touched

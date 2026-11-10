-- operator: slice
-- question: Which category groups can the slice page offer?
-- requirement: R25
-- tables: gold.dim_product

SELECT DISTINCT p.category_group
FROM {catalog}.{gold}.dim_product AS p
WHERE p.product_key <> -1
  AND p.category_group IS NOT NULL
ORDER BY p.category_group

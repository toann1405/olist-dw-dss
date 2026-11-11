-- requirement: R37
-- tables: dss.decision_log

SELECT COALESCE(MAX(decision_id), 0) AS max_id
FROM {catalog}.{dss}.decision_log

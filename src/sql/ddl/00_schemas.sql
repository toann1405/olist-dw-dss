-- Schemas for the Phase 3 cloud ETL. {catalog} is replaced by the setup widget.
-- No business tables in {dss}.

CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{bronze}`;
CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{silver}`;
CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{gold}`;
CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{dss}`;

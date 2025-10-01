BEGIN;

ALTER TABLE heating.metadata DROP COLUMN fabric_cost_total;
ALTER TABLE heating.metadata DROP COLUMN fabric_cost_breakdown;

END;

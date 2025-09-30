BEGIN;

ALTER TABLE heating.metadata ADD COLUMN fabric_cost_total FLOAT;
ALTER TABLE heating.metadata ADD COLUMN fabric_cost_breakdown JSONB;

-- If we had stored the cost as a param already, then put it to the new column now.
UPDATE heating.metadata SET fabric_cost_total = CAST(params['cost'] AS FLOAT);

END;

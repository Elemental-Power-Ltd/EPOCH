BEGIN;

ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS portfolio_range JSONB;
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS input_data JSONB;
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS site_constraints JSONB;

UPDATE optimisation.task_config AS tc
SET
    portfolio_range = sub.portfolio_range,
    input_data = sub.input_data,
    site_constraints = sub.site_constraints
FROM (
    SELECT
        task_id,
        jsonb_object_agg(site_id, site_range) AS portfolio_range,
        jsonb_object_agg(site_id, site_data) AS input_data,
        jsonb_object_agg(site_id, site_constraints) AS site_constraints
    FROM optimisation.site_task_config
    GROUP BY task_id
) AS sub
WHERE tc.task_id = sub.task_id;

DROP TABLE IF EXISTS optimisation.site_task_config;

END;
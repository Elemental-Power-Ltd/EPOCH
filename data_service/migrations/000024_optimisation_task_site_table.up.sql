BEGIN;

CREATE TABLE IF NOT EXISTS optimisation.site_task_config (
    task_id UUID NOT NULL REFERENCES optimisation.task_config (task_id),
    site_id TEXT NOT NULL,
    bundle_id UUID,
    site_range JSONB,
    site_constraints JSONB,
    site_data JSONB
);

INSERT INTO optimisation.site_task_config (task_id, site_id, site_range, site_data, site_constraints)
WITH pr AS (
    SELECT
        task_id,
        key AS site_id,
        value AS site_range
    FROM
        optimisation.task_config, jsonb_each(portfolio_range)
    WHERE
        portfolio_range IS NOT NULL AND jsonb_typeof(portfolio_range) != 'null'
),

sd AS (
    SELECT
        task_id,
        key AS site_id,
        value AS site_data
    FROM
        optimisation.task_config, jsonb_each(input_data)
    WHERE
        input_data IS NOT NULL AND jsonb_typeof(input_data) != 'null'
),

sc AS (
    SELECT
        task_id,
        key AS site_id,
        value AS constraints
    FROM
        optimisation.task_config, jsonb_each(site_constraints)
    WHERE
        site_constraints IS NOT NULL AND jsonb_typeof(site_constraints) != 'null'
)

SELECT
    tc.task_id,
    pr.site_id,
    pr.site_range,
    sd.site_data,
    sc.constraints AS site_constraints
FROM
    optimisation.task_config AS tc
LEFT JOIN pr
    ON pr.site_id = site_id AND tc.task_id = pr.task_id
LEFT JOIN sd
    ON pr.site_id = sd.site_id AND tc.task_id = sd.task_id
LEFT JOIN sc
    ON pr.site_id = sc.site_id AND tc.task_id = sc.task_id
ORDER BY tc.task_id;

ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS portfolio_range;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS input_data;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS site_constraints;

END;

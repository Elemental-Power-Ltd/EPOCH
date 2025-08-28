BEGIN;

CREATE TABLE IF NOT EXISTS optimisation.site_task_config (
    task_id UUID NOT NULL REFERENCES optimisation.task_config (task_id),
    site_id TEXT NOT NULL REFERENCES client_info.site_info (site_id),
    bundle_id UUID REFERENCES data_bundles.metadata (bundle_id),
    site_range JSONB,
    site_constraints JSONB,
    site_data JSONB
);

INSERT INTO optimisation.site_task_config (task_id, site_id, site_range, site_data, site_constraints)
WITH pr AS (
    SELECT
        tc.task_id,
        prj.key AS site_id,
        prj.value AS site_range
    FROM
        optimisation.task_config AS tc, jsonb_each(tc.portfolio_range) AS prj
    WHERE
        tc.portfolio_range IS NOT NULL AND jsonb_typeof(tc.portfolio_range) != 'null'
),

sd AS (
    SELECT
        tc.task_id,
        sdj.key AS site_id,
        sdj.value AS site_data
    FROM
        optimisation.task_config AS tc, jsonb_each(tc.input_data) AS sdj
    WHERE
        tc.input_data IS NOT NULL AND jsonb_typeof(tc.input_data) != 'null'
),

sc AS (
    SELECT
        tc.task_id,
        scj.key AS site_id,
        scj.value AS constr
    FROM
        optimisation.task_config AS tc, jsonb_each(tc.site_constraints) AS scj
    WHERE
        tc.site_constraints IS NOT NULL AND jsonb_typeof(tc.site_constraints) != 'null'
)

SELECT
    tc.task_id,
    pr.site_id,
    pr.site_range,
    sd.site_data,
    sc.constr AS site_constraints
FROM
    optimisation.task_config AS tc
LEFT JOIN pr
    ON tc.task_id = pr.task_id
LEFT JOIN sd
    ON pr.site_id = sd.site_id AND tc.task_id = sd.task_id
LEFT JOIN sc
    ON pr.site_id = sc.site_id AND tc.task_id = sc.task_id
ORDER BY tc.task_id;

ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS portfolio_range;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS input_data;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS site_constraints;

END;

BEGIN;

ALTER TABLE optimisation.task_config DROP COLUMN baseline_id;
DROP TABLE client_info.site_baselines;

END;

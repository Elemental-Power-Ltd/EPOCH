BEGIN;

DROP TABLE client_info.site_baselines;

ALTER TABLE optimisation.task_config DROP COLUMN baseline_id;

END;

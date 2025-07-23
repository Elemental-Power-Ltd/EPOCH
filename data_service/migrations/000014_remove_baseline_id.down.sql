BEGIN;

ALTER TABLE optimisation.task_config ADD COLUMN baseline_id UUID REFERENCES client_info.site_baselines (baseline_id);

END;

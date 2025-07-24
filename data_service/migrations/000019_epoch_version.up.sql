BEGIN;

ALTER TABLE optimisation.task_config ADD COLUMN epoch_version TEXT;

END;

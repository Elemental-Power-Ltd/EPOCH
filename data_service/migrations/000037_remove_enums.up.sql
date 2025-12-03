BEGIN;

DROP TYPE public.stdortou; -- noqa: CP05
ALTER TABLE ONLY optimisation.task_config DROP CONSTRAINT fk_job_config_optimiser_type_optimiser_name;
ALTER TABLE ONLY optimisation.optimisers DROP CONSTRAINT optimisers_pkey;
DROP TABLE optimisation.optimisers;

END;

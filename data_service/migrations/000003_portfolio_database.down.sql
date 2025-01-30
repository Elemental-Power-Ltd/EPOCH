BEGIN;

ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS objectives;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS portfolio_constraints;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS site_constraints;
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS objective_directions objective_t;
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS constraints_min objective_t;
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS constraints_max objective_t;
ALTER TABLE optimisation.task_config RENAME portfolio_range TO parameters; 

CREATE TABLE IF NOT EXISTS optimisation.results (
    task_id uuid,
    site_id text,
    solutions jsonb NOT NULL,
    objective_values public.objective_t NOT NULL,
    n_evals integer,
    exec_time interval,
    completed_at timestamp with time zone DEFAULT now() NOT NULL,
    results_id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    CONSTRAINT results_n_evals_check CHECK ((n_evals > 0))
);

DROP TABLE IF EXISTS optimisation.task_results;
DROP TABLE IF EXISTS optimisation.site_results;
DROP TABLE IF EXISTS optimisation.portfolio_results;



END;
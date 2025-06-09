BEGIN;

ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS objectives;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS portfolio_constraints;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS site_constraints;
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS objective_directions OBJECTIVE_T;
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS constraints_min OBJECTIVE_T;
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS constraints_max OBJECTIVE_T;
ALTER TABLE optimisation.task_config RENAME portfolio_range TO parameters;

CREATE TABLE IF NOT EXISTS optimisation.results (
    task_id UUID,
    site_id TEXT,
    solutions JSONB NOT NULL,
    objective_values public.OBJECTIVE_T NOT NULL,
    n_evals INTEGER,
    exec_time INTERVAL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    results_id UUID NOT NULL,
    portfolio_id UUID NOT NULL,
    CONSTRAINT results_n_evals_check CHECK ((n_evals > 0))
);

DROP TABLE IF EXISTS optimisation.task_results;
DROP TABLE IF EXISTS optimisation.site_results;
DROP TABLE IF EXISTS optimisation.portfolio_results;

END;

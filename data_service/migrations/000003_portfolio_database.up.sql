BEGIN;

ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS objectives JSONB; -- expected to be a list of objectives
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS portfolio_constraints JSONB;
ALTER TABLE optimisation.task_config ADD COLUMN IF NOT EXISTS site_constraints JSONB;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS objective_directions;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS constraints_min;
ALTER TABLE optimisation.task_config DROP COLUMN IF EXISTS constraints_max;
ALTER TABLE optimisation.task_config RENAME parameters TO portfolio_range; 

DROP TABLE IF EXISTS optimisation.results;

CREATE TABLE IF NOT EXISTS optimisation.task_results (
    task_id uuid NOT NULL REFERENCES optimisation.task_config(task_id),
    n_evals integer,
    exec_time interval,
    completed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT results_n_evals_check CHECK ((n_evals > 0))
);

CREATE TABLE IF NOT EXISTS optimisation.portfolio_results (
    task_id uuid NOT NULL REFERENCES optimisation.task_config(task_id),
    portfolio_id uuid PRIMARY KEY,
    metric_carbon_balance_scope_1 double precision,
    metric_carbon_balance_scope_2 double precision,
    metric_cost_balance double precision,
    metric_capex double precision,
    metric_payback_horizon double precision,
    metric_annualised_cost double precision
);

CREATE TABLE IF NOT EXISTS optimisation.site_results (
    portfolio_id uuid NOT NULL REFERENCES optimisation.portfolio_results(portfolio_id),
    site_id TEXT NOT NULL REFERENCES client_info.site_info(site_id), -- note that this won't allow for dummy sites
    metric_carbon_balance_scope_1 double precision,
    metric_carbon_balance_scope_2 double precision,
    metric_cost_balance double precision,
    metric_capex double precision,
    metric_payback_horizon double precision,
    metric_annualised_cost double precision,
    PRIMARY KEY(portfolio_id, site_id)
);

END;
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
    task_id UUID NOT NULL REFERENCES optimisation.task_config (task_id),
    n_evals INTEGER,
    exec_time INTERVAL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT results_n_evals_check CHECK ((n_evals > 0))
);

CREATE TABLE IF NOT EXISTS optimisation.portfolio_results (
    task_id UUID NOT NULL REFERENCES optimisation.task_config (task_id),
    portfolio_id UUID PRIMARY KEY,
    metric_carbon_balance_scope_1 DOUBLE PRECISION,
    metric_carbon_balance_scope_2 DOUBLE PRECISION,
    metric_cost_balance DOUBLE PRECISION,
    metric_capex DOUBLE PRECISION,
    metric_payback_horizon DOUBLE PRECISION,
    metric_annualised_cost DOUBLE PRECISION,
    metric_carbon_cost DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS optimisation.site_results (
    portfolio_id UUID NOT NULL REFERENCES optimisation.portfolio_results (portfolio_id),
    site_id TEXT NOT NULL REFERENCES client_info.site_info (site_id), -- note that this won't allow for dummy sites
    scenario JSONB,
    metric_carbon_balance_scope_1 DOUBLE PRECISION,
    metric_carbon_balance_scope_2 DOUBLE PRECISION,
    metric_cost_balance DOUBLE PRECISION,
    metric_capex DOUBLE PRECISION,
    metric_payback_horizon DOUBLE PRECISION,
    metric_annualised_cost DOUBLE PRECISION,
    metric_carbon_cost DOUBLE PRECISION,
    PRIMARY KEY (portfolio_id, site_id)
);

END;

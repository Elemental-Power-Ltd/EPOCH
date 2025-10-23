BEGIN;

CREATE TABLE IF NOT EXISTS optimisation.curated_results (
    highlight_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES optimisation.task_config (task_id),
    portfolio_id UUID NOT NULL REFERENCES optimisation.portfolio_results (portfolio_id),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    display_name TEXT NOT NULL
);

END;

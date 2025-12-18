BEGIN;

CREATE TABLE IF NOT EXISTS optimisation.cost_models (
    cost_model_id UUID PRIMARY KEY,
    model_name TEXT,
    capex_model JSONB,
    opex_model JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE optimisation.site_task_config ADD COLUMN site_config JSONB;

END;

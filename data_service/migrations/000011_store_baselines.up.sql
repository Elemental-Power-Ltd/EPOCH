BEGIN;

CREATE TABLE client_info.site_baselines (
    baseline_id UUID PRIMARY KEY,
    site_id TEXT NOT NULL,
    baseline JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    FOREIGN KEY (site_id)
    REFERENCES client_info.site_info (site_id)
);

ALTER TABLE optimisation.task_config ADD COLUMN baseline_id UUID REFERENCES client_info.site_baselines (baseline_id);

END;

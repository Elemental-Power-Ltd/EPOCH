BEGIN;

CREATE TABLE client_info.site_baselines (
    site_id TEXT NOT NULL,
    baseline JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    FOREIGN KEY (site_id)
    REFERENCES client_info.site_info (site_id)
);

END;
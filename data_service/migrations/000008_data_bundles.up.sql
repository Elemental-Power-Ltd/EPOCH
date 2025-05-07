BEGIN;

CREATE SCHEMA IF NOT EXISTS data_bundles;

CREATE TABLE data_bundles.metadata (
    bundle_id UUID NOT NULL,
    name TEXT,
    site_id TEXT REFERENCES client_info.site_info (site_id),
    start_ts TIMESTAMPTZ,
    end_ts TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (bundle_id)
);

CREATE TABLE data_bundles.dataset_links (
    bundle_id UUID NOT NULL REFERENCES data_bundles.metadata (bundle_id),
    dataset_type TEXT,
    dataset_id UUID
);

END;

BEGIN;

CREATE SCHEMA job_queue;
CREATE TABLE IF NOT EXISTS job_queue.job_status (
    job_id SERIAL PRIMARY KEY,
    job_type TEXT NOT NULL,
    job_status TEXT NOT NULL,
    bundle_id UUID REFERENCES data_bundles.metadata (bundle_id),
    request JSONB,
    detail TEXT,
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
CREATE INDEX job_queue_job_status_bundle_id_idx ON job_queue.job_status USING btree (bundle_id);

END;

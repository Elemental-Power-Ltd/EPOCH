BEGIN;

ALTER TABLE tariffs.electricity RENAME COLUMN timestamp TO start_ts;
ALTER TABLE tariffs.electricity ADD end_ts TIMESTAMPTZ;
UPDATE tariffs.electricity SET end_ts = start_ts + INTERVAL '1 hour';

END;
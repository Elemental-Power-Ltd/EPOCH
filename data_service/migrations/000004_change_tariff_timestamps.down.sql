BEGIN;

ALTER TABLE tariffs.electricity RENAME COLUMN start_ts TO timestamp;
ALTER TABLE tariffs.electricity DROP COLUMN end_ts;

END;

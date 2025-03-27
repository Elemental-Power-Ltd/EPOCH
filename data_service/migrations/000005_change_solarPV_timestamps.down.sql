BEGIN;

ALTER TABLE renewables.solar_pv RENAME COLUMN start_ts TO timestamp;
ALTER TABLE renewables.solar_pv DROP COLUMN end_ts;

END;

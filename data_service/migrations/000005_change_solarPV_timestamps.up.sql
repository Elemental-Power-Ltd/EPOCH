BEGIN;

ALTER TABLE renewables.solar_pv RENAME COLUMN timestamp TO start_ts;
ALTER TABLE renewables.solar_pv ADD end_ts TIMESTAMPTZ;
UPDATE renewables.solar_pv SET end_ts = start_ts + INTERVAL '1 hour';

END;

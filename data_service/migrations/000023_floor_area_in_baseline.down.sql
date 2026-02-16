-- This linting rule is particularly awkawrd here, so ignore it
-- noqa: disable=LT14

-- This effectively remakes 000021_floor_area.up.sql as we lost that data in the up migration 23
BEGIN;
-- This is in m^2, and may differ to the floor area calculated in PHPPs
-- Use this floor area for official metrics like carbon intensity per floor area, or SAP rating.
ALTER TABLE client_info.site_info ADD COLUMN floor_area FLOAT;

-- Get rid of the extra JSON keys
UPDATE client_info.site_baselines AS sb
SET baseline['building'] = baseline['building'] - 'floor_area'
WHERE baseline ? 'building';

END;

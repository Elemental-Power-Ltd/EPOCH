BEGIN;
-- This is in m^2, and may differ to the floor area calculated in PHPPs
-- Use this floor area for official metrics like carbon intensity per floor area, or SAP rating.
ALTER TABLE client_info.site_info ADD COLUMN floor_area FLOAT;

END;

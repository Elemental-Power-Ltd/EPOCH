BEGIN;

DROP TABLE client_info.solar_locations;

-- We know that we'll almost always be querying on the site ID so use that as our index.
DROP INDEX client_info_solar_locations_site_id_idx;

ALTER TABLE renewables.metadata
DROP COLUMN renewables_location_id;

END;

BEGIN;

ALTER TABLE renewables.metadata
DROP COLUMN renewables_location_id;

DROP INDEX client_info.client_info_solar_locations_site_id_idx;
DROP TABLE client_info.solar_locations;

END;

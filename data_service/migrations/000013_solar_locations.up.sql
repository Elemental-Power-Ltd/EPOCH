BEGIN;

CREATE TABLE client_info.solar_locations (
    renewables_location_id TEXT PRIMARY KEY,
    name TEXT,
    site_id TEXT NOT NULL REFERENCES client_info.site_info (site_id),
    mounting_type TEXT DEFAULT 'building-integrated',
    tilt DOUBLE PRECISION,
    azimuth DOUBLE PRECISION,
    maxpower DOUBLE PRECISION
);

-- We know that we'll almost always be querying on the site ID so use that as our index.
CREATE INDEX client_info_solar_locations_site_id_idx ON client_info.solar_locations (site_id);

ALTER TABLE renewables.metadata
ADD COLUMN renewables_location_id TEXT REFERENCES client_info.solar_locations (renewables_location_id);

END;

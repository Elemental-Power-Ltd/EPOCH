BEGIN;

ALTER TABLE heating.metadata ADD COLUMN peak_hload FLOAT;

CREATE TABLE heating.structure_metadata (
    structure_id UUID PRIMARY KEY,
    site_id TEXT NOT NULL REFERENCES client_info.site_info (site_id),
    internal_volume DOUBLE PRECISION,
    air_changes DOUBLE PRECISION,
    floor_area DOUBLE PRECISION,
    filename TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE heating.structure_elements (
    structure_id UUID REFERENCES heating.structure_metadata (structure_id),
    element_id INTEGER,
    element_name TEXT,
    element_group TEXT,
    area DOUBLE PRECISION,
    angle DOUBLE PRECISION,
    u_value DOUBLE PRECISION,
    area_type TEXT
);

END;

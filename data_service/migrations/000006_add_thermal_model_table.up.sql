BEGIN;

CREATE TABLE heating.thermal_model (
    dataset_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    site_id TEXT,
    results JSONB,
    datasets JSONB,
    PRIMARY KEY (dataset_id),
    CONSTRAINT fk_heating_thermal_model_site_id
    FOREIGN KEY (site_id)
    REFERENCES client_info.site_info (site_id)
);

END;

BEGIN;

ALTER TABLE client_info.site_baselines ADD COLUMN tariff_id UUID REFERENCES tariffs.metadata (dataset_id);

END;
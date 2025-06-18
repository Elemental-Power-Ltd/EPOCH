BEGIN;

CREATE TABLE renewables.wind (
    dataset_id uuid,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    solar_generation double precision NOT NULL
);

END;
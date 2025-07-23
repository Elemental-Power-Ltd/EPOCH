BEGIN;

CREATE TABLE renewables.wind (
    dataset_id UUID REFERENCES renewables.metadata (dataset_id),
    start_ts TIMESTAMPTZ NOT NULL,
    end_ts TIMESTAMPTZ NOT NULL,
    wind DOUBLE PRECISION NOT NULL
);

END;

BEGIN;

CREATE TABLE carbon_intensity.grid_co2_cache (
    gsp_code TEXT NOT NULL,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    forecast double precision,
    actual double precision,
    gas double precision,
    coal double precision,
    biomass double precision,
    nuclear double precision,
    hydro double precision,
    imports double precision,
    other double precision,
    wind double precision,
    solar double precision
)  PARTITION BY LIST (gsp_code);

CREATE UNIQUE INDEX carbon_intensity_grid_co2_cache_location_timestamp_idx ON ONLY carbon_intensity.grid_co2_cache USING btree (gsp_code, start_ts);

-- This section is for "national" data
CREATE TABLE carbon_intensity.grid_co2_cache_part_uk PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('uk');
CREATE TABLE carbon_intensity.grid_co2_cache_part_a PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('A');
CREATE TABLE carbon_intensity.grid_co2_cache_part_b PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('B');
CREATE TABLE carbon_intensity.grid_co2_cache_part_c PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('C');
CREATE TABLE carbon_intensity.grid_co2_cache_part_d PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('D');
CREATE TABLE carbon_intensity.grid_co2_cache_part_e PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('E');
CREATE TABLE carbon_intensity.grid_co2_cache_part_f PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('F');
CREATE TABLE carbon_intensity.grid_co2_cache_part_g PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('G');
CREATE TABLE carbon_intensity.grid_co2_cache_part_h PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('H');
CREATE TABLE carbon_intensity.grid_co2_cache_part_k PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('K');
CREATE TABLE carbon_intensity.grid_co2_cache_part_l PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('L');
CREATE TABLE carbon_intensity.grid_co2_cache_part_m PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('M');
CREATE TABLE carbon_intensity.grid_co2_cache_part_n PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('N');
CREATE TABLE carbon_intensity.grid_co2_cache_part_p PARTITION OF carbon_intensity.grid_co2_cache FOR VALUES IN ('P');




END;
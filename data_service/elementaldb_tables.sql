--
-- PostgreSQL database dump
--

-- Dumped from database version 14.13 (Ubuntu 14.13-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.13 (Ubuntu 14.13-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: carbon_intensity; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA carbon_intensity;


--
-- Name: client_info; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA client_info;


--
-- Name: client_meters; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA client_meters;


--
-- Name: heating; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA heating;


--
-- Name: optimisation; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA optimisation;


--
-- Name: renewables; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA renewables;


--
-- Name: tariffs; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA tariffs;


--
-- Name: weather; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA weather;


--
-- Name: latlon; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.latlon AS (
	lat double precision,
	lon double precision
);


--
-- Name: objective_t; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.objective_t AS (
	carbon_balance double precision,
	cost_balance double precision,
	capex double precision,
	payback_horizon double precision,
	annualised_cost double precision
);


--
-- Name: stdortou; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.stdortou AS ENUM (
    'Std',
    'ToU'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: grid_co2; Type: TABLE; Schema: carbon_intensity; Owner: -
--

CREATE TABLE carbon_intensity.grid_co2 (
    dataset_id uuid,
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
);


--
-- Name: metadata; Type: TABLE; Schema: carbon_intensity; Owner: -
--

CREATE TABLE carbon_intensity.metadata (
    dataset_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    data_source text,
    is_regional boolean,
    site_id text,
    deleted_at timestamp with time zone
);


--
-- Name: clients; Type: TABLE; Schema: client_info; Owner: -
--

CREATE TABLE client_info.clients (
    client_id text NOT NULL,
    name text
);


--
-- Name: site_info; Type: TABLE; Schema: client_info; Owner: -
--

CREATE TABLE client_info.site_info (
    site_id text NOT NULL,
    name text,
    address text,
    location text,
    coordinates public.latlon,
    client_id text
);


--
-- Name: electricity_meters; Type: TABLE; Schema: client_meters; Owner: -
--

CREATE TABLE client_meters.electricity_meters (
    dataset_id uuid,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    consumption_kwh double precision,
    unit_cost numeric(19,4),
    total_cost numeric(19,4)
);


--
-- Name: electricity_meters_synthesised; Type: TABLE; Schema: client_meters; Owner: -
--

CREATE TABLE client_meters.electricity_meters_synthesised (
    dataset_id uuid,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    consumption_kwh double precision
);


--
-- Name: gas_meters; Type: TABLE; Schema: client_meters; Owner: -
--

CREATE TABLE client_meters.gas_meters (
    dataset_id uuid,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    consumption_kwh double precision,
    consumption_m3 double precision,
    unit_cost numeric(19,4),
    total_cost numeric(19,4)
);


--
-- Name: metadata; Type: TABLE; Schema: client_meters; Owner: -
--

CREATE TABLE client_meters.metadata (
    dataset_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    site_id text NOT NULL,
    deleted_at timestamp with time zone,
    fuel_type text NOT NULL,
    reading_type text,
    filename text,
    is_synthesised boolean DEFAULT false,
    CONSTRAINT metadata_fuel_type_check CHECK ((fuel_type = ANY (ARRAY['gas'::text, 'elec'::text, 'oil'::text]))),
    CONSTRAINT metadata_reading_type_check CHECK ((reading_type = ANY (ARRAY['halfhourly'::text, 'manual'::text, 'automatic'::text])))
);


--
-- Name: fabric_interventions; Type: TABLE; Schema: heating; Owner: -
--

CREATE TABLE heating.fabric_interventions (
    site_id text NOT NULL,
    intervention text NOT NULL,
    cost numeric(15,6)
);


--
-- Name: interventions; Type: TABLE; Schema: heating; Owner: -
--

CREATE TABLE heating.interventions (
    site_id text NOT NULL,
    intervention text NOT NULL,
    cost numeric(15,4)
);


--
-- Name: metadata; Type: TABLE; Schema: heating; Owner: -
--

CREATE TABLE heating.metadata (
    dataset_id uuid NOT NULL,
    site_id text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    params jsonb,
    interventions text[]
);


--
-- Name: synthesised; Type: TABLE; Schema: heating; Owner: -
--

CREATE TABLE heating.synthesised (
    dataset_id uuid NOT NULL,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    heating double precision,
    dhw double precision,
    air_temperature double precision
);


--
-- Name: optimisers; Type: TABLE; Schema: optimisation; Owner: -
--

CREATE TABLE optimisation.optimisers (
    name text NOT NULL
);


--
-- Name: results; Type: TABLE; Schema: optimisation; Owner: -
--

CREATE TABLE optimisation.results (
    task_id uuid,
    solutions jsonb NOT NULL,
    objective_values public.objective_t NOT NULL,
    n_evals integer,
    exec_time interval,
    completed_at timestamp with time zone DEFAULT now() NOT NULL,
    results_id uuid NOT NULL,
    CONSTRAINT results_n_evals_check CHECK ((n_evals > 0))
);


--
-- Name: task_config; Type: TABLE; Schema: optimisation; Owner: -
--

CREATE TABLE optimisation.task_config (
    task_id uuid NOT NULL,
    task_name text,
    objective_directions public.objective_t NOT NULL,
    constraints_min public.objective_t,
    constraints_max public.objective_t,
    parameters jsonb,
    input_data jsonb,
    optimiser_type text NOT NULL,
    optimiser_hyperparameters jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    site_id text
);


--
-- Name: metadata; Type: TABLE; Schema: renewables; Owner: -
--

CREATE TABLE renewables.metadata (
    dataset_id uuid NOT NULL,
    site_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    data_source text,
    parameters jsonb
);


--
-- Name: metadata; Type: TABLE; Schema: tariffs; Owner: -
--

CREATE TABLE tariffs.metadata (
    dataset_id uuid NOT NULL,
    site_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    provider text,
    product_name text,
    tariff_name text,
    valid_from timestamp with time zone,
    valid_to timestamp with time zone
);


--
-- Name: all_metadata; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.all_metadata AS
 SELECT u.dataset_id,
    u.created_at,
    u.dataset_type,
    u.site_id
   FROM ( SELECT metadata.dataset_id,
            metadata.created_at,
                CASE
                    WHEN (metadata.fuel_type = 'elec'::text) THEN 'ElectricityMeter'::text
                    WHEN (metadata.fuel_type = 'gas'::text) THEN 'GasMeter'::text
                    ELSE NULL::text
                END AS dataset_type,
            metadata.site_id
           FROM client_meters.metadata
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'ImportTariff'::text AS dataset_type,
            metadata.site_id
           FROM tariffs.metadata
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'RenewablesGeneration'::text AS dataset_type,
            metadata.site_id
           FROM renewables.metadata
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'HeatingLoad'::text AS dataset_type,
            metadata.site_id
           FROM heating.metadata) u
  ORDER BY u.created_at;


--
-- Name: combined_dataset_metadata; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.combined_dataset_metadata AS
 SELECT u.dataset_id,
    u.created_at,
    u.dataset_type,
    u.site_id
   FROM ( SELECT metadata.dataset_id,
            metadata.created_at,
                CASE
                    WHEN (metadata.fuel_type = 'elec'::text) THEN 'ElectricityMeterData'::text
                    WHEN (metadata.fuel_type = 'gas'::text) THEN 'GasMeterData'::text
                    ELSE NULL::text
                END AS dataset_type,
            metadata.site_id
           FROM client_meters.metadata
          WHERE (metadata.is_synthesised = false)
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'ElectricityMeterDataSynthesised'::text AS dataset_type,
            metadata.site_id
           FROM client_meters.metadata
          WHERE ((metadata.is_synthesised = true) AND (metadata.fuel_type = 'gas'::text))
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'ImportTariff'::text AS dataset_type,
            metadata.site_id
           FROM tariffs.metadata
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'RenewablesGeneration'::text AS dataset_type,
            metadata.site_id
           FROM renewables.metadata
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'HeatingLoad'::text AS dataset_type,
            metadata.site_id
           FROM heating.metadata
        UNION ALL
         SELECT metadata.dataset_id,
            metadata.created_at,
            'CarbonIntensity'::text AS dataset_type,
            metadata.site_id
           FROM carbon_intensity.metadata
        UNION ALL
         SELECT gen_random_uuid() AS dataset_id,
            now() AS created_at,
            'ASHPData'::text AS dataset_type,
            si.site_id
           FROM ( SELECT DISTINCT site_info.site_id
                   FROM client_info.site_info) si) u
  ORDER BY u.created_at;


--
-- Name: solar_pv; Type: TABLE; Schema: renewables; Owner: -
--

CREATE TABLE renewables.solar_pv (
    dataset_id uuid,
    "timestamp" timestamp with time zone NOT NULL,
    solar_generation double precision NOT NULL
);


--
-- Name: electricity; Type: TABLE; Schema: tariffs; Owner: -
--

CREATE TABLE tariffs.electricity (
    dataset_id uuid,
    "timestamp" timestamp with time zone NOT NULL,
    unit_cost numeric(15,4),
    flat_cost numeric(15,5)
);


--
-- Name: visual_crossing; Type: TABLE; Schema: weather; Owner: -
--

CREATE TABLE weather.visual_crossing (
    "timestamp" timestamp with time zone NOT NULL,
    location text NOT NULL,
    temp double precision,
    humidity double precision,
    precip double precision,
    precipprob double precision,
    snow double precision,
    snowdepth double precision,
    windgust double precision,
    windspeed double precision,
    winddir double precision,
    pressure double precision,
    cloudcover double precision,
    solarradiation double precision,
    solarenergy double precision,
    dniradiation double precision,
    difradiation double precision
)
PARTITION BY HASH (location);


--
-- Name: visual_crossing_part_0; Type: TABLE; Schema: weather; Owner: -
--

CREATE TABLE weather.visual_crossing_part_0 (
    "timestamp" timestamp with time zone NOT NULL,
    location text NOT NULL,
    temp double precision,
    humidity double precision,
    precip double precision,
    precipprob double precision,
    snow double precision,
    snowdepth double precision,
    windgust double precision,
    windspeed double precision,
    winddir double precision,
    pressure double precision,
    cloudcover double precision,
    solarradiation double precision,
    solarenergy double precision,
    dniradiation double precision,
    difradiation double precision
);


--
-- Name: visual_crossing_part_1; Type: TABLE; Schema: weather; Owner: -
--

CREATE TABLE weather.visual_crossing_part_1 (
    "timestamp" timestamp with time zone NOT NULL,
    location text NOT NULL,
    temp double precision,
    humidity double precision,
    precip double precision,
    precipprob double precision,
    snow double precision,
    snowdepth double precision,
    windgust double precision,
    windspeed double precision,
    winddir double precision,
    pressure double precision,
    cloudcover double precision,
    solarradiation double precision,
    solarenergy double precision,
    dniradiation double precision,
    difradiation double precision
);


--
-- Name: visual_crossing_part_2; Type: TABLE; Schema: weather; Owner: -
--

CREATE TABLE weather.visual_crossing_part_2 (
    "timestamp" timestamp with time zone NOT NULL,
    location text NOT NULL,
    temp double precision,
    humidity double precision,
    precip double precision,
    precipprob double precision,
    snow double precision,
    snowdepth double precision,
    windgust double precision,
    windspeed double precision,
    winddir double precision,
    pressure double precision,
    cloudcover double precision,
    solarradiation double precision,
    solarenergy double precision,
    dniradiation double precision,
    difradiation double precision
);


--
-- Name: visual_crossing_part_3; Type: TABLE; Schema: weather; Owner: -
--

CREATE TABLE weather.visual_crossing_part_3 (
    "timestamp" timestamp with time zone NOT NULL,
    location text NOT NULL,
    temp double precision,
    humidity double precision,
    precip double precision,
    precipprob double precision,
    snow double precision,
    snowdepth double precision,
    windgust double precision,
    windspeed double precision,
    winddir double precision,
    pressure double precision,
    cloudcover double precision,
    solarradiation double precision,
    solarenergy double precision,
    dniradiation double precision,
    difradiation double precision
);


--
-- Name: visual_crossing_part_4; Type: TABLE; Schema: weather; Owner: -
--

CREATE TABLE weather.visual_crossing_part_4 (
    "timestamp" timestamp with time zone NOT NULL,
    location text NOT NULL,
    temp double precision,
    humidity double precision,
    precip double precision,
    precipprob double precision,
    snow double precision,
    snowdepth double precision,
    windgust double precision,
    windspeed double precision,
    winddir double precision,
    pressure double precision,
    cloudcover double precision,
    solarradiation double precision,
    solarenergy double precision,
    dniradiation double precision,
    difradiation double precision
);


--
-- Name: visual_crossing_part_5; Type: TABLE; Schema: weather; Owner: -
--

CREATE TABLE weather.visual_crossing_part_5 (
    "timestamp" timestamp with time zone NOT NULL,
    location text NOT NULL,
    temp double precision,
    humidity double precision,
    precip double precision,
    precipprob double precision,
    snow double precision,
    snowdepth double precision,
    windgust double precision,
    windspeed double precision,
    winddir double precision,
    pressure double precision,
    cloudcover double precision,
    solarradiation double precision,
    solarenergy double precision,
    dniradiation double precision,
    difradiation double precision
);


--
-- Name: visual_crossing_part_6; Type: TABLE; Schema: weather; Owner: -
--

CREATE TABLE weather.visual_crossing_part_6 (
    "timestamp" timestamp with time zone NOT NULL,
    location text NOT NULL,
    temp double precision,
    humidity double precision,
    precip double precision,
    precipprob double precision,
    snow double precision,
    snowdepth double precision,
    windgust double precision,
    windspeed double precision,
    winddir double precision,
    pressure double precision,
    cloudcover double precision,
    solarradiation double precision,
    solarenergy double precision,
    dniradiation double precision,
    difradiation double precision
);


--
-- Name: visual_crossing_part_7; Type: TABLE; Schema: weather; Owner: -
--

CREATE TABLE weather.visual_crossing_part_7 (
    "timestamp" timestamp with time zone NOT NULL,
    location text NOT NULL,
    temp double precision,
    humidity double precision,
    precip double precision,
    precipprob double precision,
    snow double precision,
    snowdepth double precision,
    windgust double precision,
    windspeed double precision,
    winddir double precision,
    pressure double precision,
    cloudcover double precision,
    solarradiation double precision,
    solarenergy double precision,
    dniradiation double precision,
    difradiation double precision
);


--
-- Name: visual_crossing_part_0; Type: TABLE ATTACH; Schema: weather; Owner: -
--

ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_0 FOR VALUES WITH (modulus 8, remainder 0);


--
-- Name: visual_crossing_part_1; Type: TABLE ATTACH; Schema: weather; Owner: -
--

ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_1 FOR VALUES WITH (modulus 8, remainder 1);


--
-- Name: visual_crossing_part_2; Type: TABLE ATTACH; Schema: weather; Owner: -
--

ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_2 FOR VALUES WITH (modulus 8, remainder 2);


--
-- Name: visual_crossing_part_3; Type: TABLE ATTACH; Schema: weather; Owner: -
--

ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_3 FOR VALUES WITH (modulus 8, remainder 3);


--
-- Name: visual_crossing_part_4; Type: TABLE ATTACH; Schema: weather; Owner: -
--

ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_4 FOR VALUES WITH (modulus 8, remainder 4);


--
-- Name: visual_crossing_part_5; Type: TABLE ATTACH; Schema: weather; Owner: -
--

ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_5 FOR VALUES WITH (modulus 8, remainder 5);


--
-- Name: visual_crossing_part_6; Type: TABLE ATTACH; Schema: weather; Owner: -
--

ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_6 FOR VALUES WITH (modulus 8, remainder 6);


--
-- Name: visual_crossing_part_7; Type: TABLE ATTACH; Schema: weather; Owner: -
--

ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_7 FOR VALUES WITH (modulus 8, remainder 7);


--
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: carbon_intensity; Owner: -
--

ALTER TABLE ONLY carbon_intensity.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: client_info; Owner: -
--

ALTER TABLE ONLY client_info.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (client_id);


--
-- Name: site_info site_info_pkey; Type: CONSTRAINT; Schema: client_info; Owner: -
--

ALTER TABLE ONLY client_info.site_info
    ADD CONSTRAINT site_info_pkey PRIMARY KEY (site_id);


--
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: client_meters; Owner: -
--

ALTER TABLE ONLY client_meters.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);


--
-- Name: fabric_interventions fabric_interventions_pkey; Type: CONSTRAINT; Schema: heating; Owner: -
--

ALTER TABLE ONLY heating.fabric_interventions
    ADD CONSTRAINT fabric_interventions_pkey PRIMARY KEY (site_id, intervention);


--
-- Name: interventions interventions_pkey; Type: CONSTRAINT; Schema: heating; Owner: -
--

ALTER TABLE ONLY heating.interventions
    ADD CONSTRAINT interventions_pkey PRIMARY KEY (site_id, intervention);


--
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: heating; Owner: -
--

ALTER TABLE ONLY heating.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);


--
-- Name: task_config job_config_pkey; Type: CONSTRAINT; Schema: optimisation; Owner: -
--

ALTER TABLE ONLY optimisation.task_config
    ADD CONSTRAINT job_config_pkey PRIMARY KEY (task_id);


--
-- Name: optimisers optimisers_pkey; Type: CONSTRAINT; Schema: optimisation; Owner: -
--

ALTER TABLE ONLY optimisation.optimisers
    ADD CONSTRAINT optimisers_pkey PRIMARY KEY (name);


--
-- Name: results results_pkey; Type: CONSTRAINT; Schema: optimisation; Owner: -
--

ALTER TABLE ONLY optimisation.results
    ADD CONSTRAINT results_pkey PRIMARY KEY (results_id);


--
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: renewables; Owner: -
--

ALTER TABLE ONLY renewables.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);


--
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: tariffs; Owner: -
--

ALTER TABLE ONLY tariffs.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);


--
-- Name: electricity_meters_idx; Type: INDEX; Schema: client_meters; Owner: -
--

CREATE INDEX electricity_meters_idx ON client_meters.electricity_meters USING btree (dataset_id, start_ts);


--
-- Name: gas_meters_idx; Type: INDEX; Schema: client_meters; Owner: -
--

CREATE INDEX gas_meters_idx ON client_meters.gas_meters USING btree (dataset_id, start_ts);


--
-- Name: visual_crossing_loc_timestamp; Type: INDEX; Schema: weather; Owner: -
--

CREATE UNIQUE INDEX visual_crossing_loc_timestamp ON ONLY weather.visual_crossing USING btree (location, "timestamp");


--
-- Name: visual_crossing_part_0_location_timestamp_idx; Type: INDEX; Schema: weather; Owner: -
--

CREATE UNIQUE INDEX visual_crossing_part_0_location_timestamp_idx ON weather.visual_crossing_part_0 USING btree (location, "timestamp");


--
-- Name: visual_crossing_part_1_location_timestamp_idx; Type: INDEX; Schema: weather; Owner: -
--

CREATE UNIQUE INDEX visual_crossing_part_1_location_timestamp_idx ON weather.visual_crossing_part_1 USING btree (location, "timestamp");


--
-- Name: visual_crossing_part_2_location_timestamp_idx; Type: INDEX; Schema: weather; Owner: -
--

CREATE UNIQUE INDEX visual_crossing_part_2_location_timestamp_idx ON weather.visual_crossing_part_2 USING btree (location, "timestamp");


--
-- Name: visual_crossing_part_3_location_timestamp_idx; Type: INDEX; Schema: weather; Owner: -
--

CREATE UNIQUE INDEX visual_crossing_part_3_location_timestamp_idx ON weather.visual_crossing_part_3 USING btree (location, "timestamp");


--
-- Name: visual_crossing_part_4_location_timestamp_idx; Type: INDEX; Schema: weather; Owner: -
--

CREATE UNIQUE INDEX visual_crossing_part_4_location_timestamp_idx ON weather.visual_crossing_part_4 USING btree (location, "timestamp");


--
-- Name: visual_crossing_part_5_location_timestamp_idx; Type: INDEX; Schema: weather; Owner: -
--

CREATE UNIQUE INDEX visual_crossing_part_5_location_timestamp_idx ON weather.visual_crossing_part_5 USING btree (location, "timestamp");


--
-- Name: visual_crossing_part_6_location_timestamp_idx; Type: INDEX; Schema: weather; Owner: -
--

CREATE UNIQUE INDEX visual_crossing_part_6_location_timestamp_idx ON weather.visual_crossing_part_6 USING btree (location, "timestamp");


--
-- Name: visual_crossing_part_7_location_timestamp_idx; Type: INDEX; Schema: weather; Owner: -
--

CREATE UNIQUE INDEX visual_crossing_part_7_location_timestamp_idx ON weather.visual_crossing_part_7 USING btree (location, "timestamp");


--
-- Name: visual_crossing_part_0_location_timestamp_idx; Type: INDEX ATTACH; Schema: weather; Owner: -
--

ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_0_location_timestamp_idx;


--
-- Name: visual_crossing_part_1_location_timestamp_idx; Type: INDEX ATTACH; Schema: weather; Owner: -
--

ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_1_location_timestamp_idx;


--
-- Name: visual_crossing_part_2_location_timestamp_idx; Type: INDEX ATTACH; Schema: weather; Owner: -
--

ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_2_location_timestamp_idx;


--
-- Name: visual_crossing_part_3_location_timestamp_idx; Type: INDEX ATTACH; Schema: weather; Owner: -
--

ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_3_location_timestamp_idx;


--
-- Name: visual_crossing_part_4_location_timestamp_idx; Type: INDEX ATTACH; Schema: weather; Owner: -
--

ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_4_location_timestamp_idx;


--
-- Name: visual_crossing_part_5_location_timestamp_idx; Type: INDEX ATTACH; Schema: weather; Owner: -
--

ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_5_location_timestamp_idx;


--
-- Name: visual_crossing_part_6_location_timestamp_idx; Type: INDEX ATTACH; Schema: weather; Owner: -
--

ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_6_location_timestamp_idx;


--
-- Name: visual_crossing_part_7_location_timestamp_idx; Type: INDEX ATTACH; Schema: weather; Owner: -
--

ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_7_location_timestamp_idx;


--
-- Name: grid_co2 grid_co2_dataset_id_fkey; Type: FK CONSTRAINT; Schema: carbon_intensity; Owner: -
--

ALTER TABLE ONLY carbon_intensity.grid_co2
    ADD CONSTRAINT grid_co2_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES carbon_intensity.metadata(dataset_id);


--
-- Name: metadata metadata_site_id_fkey; Type: FK CONSTRAINT; Schema: carbon_intensity; Owner: -
--

ALTER TABLE ONLY carbon_intensity.metadata
    ADD CONSTRAINT metadata_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id) DEFERRABLE;


--
-- Name: site_info site_info_client_id_fkey; Type: FK CONSTRAINT; Schema: client_info; Owner: -
--

ALTER TABLE ONLY client_info.site_info
    ADD CONSTRAINT site_info_client_id_fkey FOREIGN KEY (client_id) REFERENCES client_info.clients(client_id);


--
-- Name: electricity_meters electricity_meters_dataset_id_fkey; Type: FK CONSTRAINT; Schema: client_meters; Owner: -
--

ALTER TABLE ONLY client_meters.electricity_meters
    ADD CONSTRAINT electricity_meters_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES client_meters.metadata(dataset_id);


--
-- Name: electricity_meters_synthesised electricity_meters_synthesised_dataset_id_fkey; Type: FK CONSTRAINT; Schema: client_meters; Owner: -
--

ALTER TABLE ONLY client_meters.electricity_meters_synthesised
    ADD CONSTRAINT electricity_meters_synthesised_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES client_meters.metadata(dataset_id);


--
-- Name: metadata fk_metadata_site_id; Type: FK CONSTRAINT; Schema: client_meters; Owner: -
--

ALTER TABLE ONLY client_meters.metadata
    ADD CONSTRAINT fk_metadata_site_id FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


--
-- Name: gas_meters gas_meters_dataset_id_fkey; Type: FK CONSTRAINT; Schema: client_meters; Owner: -
--

ALTER TABLE ONLY client_meters.gas_meters
    ADD CONSTRAINT gas_meters_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES client_meters.metadata(dataset_id);


--
-- Name: fabric_interventions fabric_interventions_site_id_fkey; Type: FK CONSTRAINT; Schema: heating; Owner: -
--

ALTER TABLE ONLY heating.fabric_interventions
    ADD CONSTRAINT fabric_interventions_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


--
-- Name: interventions interventions_site_id_fkey; Type: FK CONSTRAINT; Schema: heating; Owner: -
--

ALTER TABLE ONLY heating.interventions
    ADD CONSTRAINT interventions_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


--
-- Name: metadata metadata_site_id_fkey; Type: FK CONSTRAINT; Schema: heating; Owner: -
--

ALTER TABLE ONLY heating.metadata
    ADD CONSTRAINT metadata_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


--
-- Name: synthesised synthesised_dataset_id_fkey; Type: FK CONSTRAINT; Schema: heating; Owner: -
--

ALTER TABLE ONLY heating.synthesised
    ADD CONSTRAINT synthesised_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES heating.metadata(dataset_id) DEFERRABLE;


--
-- Name: task_config fk_job_config_optimiser_type_optimiser_name; Type: FK CONSTRAINT; Schema: optimisation; Owner: -
--

ALTER TABLE ONLY optimisation.task_config
    ADD CONSTRAINT fk_job_config_optimiser_type_optimiser_name FOREIGN KEY (optimiser_type) REFERENCES optimisation.optimisers(name);


--
-- Name: task_config fk_task_config_site_info_site_id; Type: FK CONSTRAINT; Schema: optimisation; Owner: -
--

ALTER TABLE ONLY optimisation.task_config
    ADD CONSTRAINT fk_task_config_site_info_site_id FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


--
-- Name: results results_id_fkey; Type: FK CONSTRAINT; Schema: optimisation; Owner: -
--

ALTER TABLE ONLY optimisation.results
    ADD CONSTRAINT results_id_fkey FOREIGN KEY (task_id) REFERENCES optimisation.task_config(task_id);


--
-- Name: metadata metadata_site_id_fkey; Type: FK CONSTRAINT; Schema: renewables; Owner: -
--

ALTER TABLE ONLY renewables.metadata
    ADD CONSTRAINT metadata_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


--
-- Name: solar_pv solar_pv_dataset_id_fkey; Type: FK CONSTRAINT; Schema: renewables; Owner: -
--

ALTER TABLE ONLY renewables.solar_pv
    ADD CONSTRAINT solar_pv_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES renewables.metadata(dataset_id);


--
-- Name: electricity electricity_dataset_id_metadata_fkey; Type: FK CONSTRAINT; Schema: tariffs; Owner: -
--

ALTER TABLE ONLY tariffs.electricity
    ADD CONSTRAINT electricity_dataset_id_metadata_fkey FOREIGN KEY (dataset_id) REFERENCES tariffs.metadata(dataset_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: metadata metadata_site_id_fkey; Type: FK CONSTRAINT; Schema: tariffs; Owner: -
--

ALTER TABLE ONLY tariffs.metadata
    ADD CONSTRAINT metadata_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


--
-- Name: SCHEMA carbon_intensity; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA carbon_intensity TO python;


--
-- Name: SCHEMA client_info; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA client_info TO python;


--
-- Name: SCHEMA client_meters; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA client_meters TO python;


--
-- Name: SCHEMA heating; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA heating TO python;


--
-- Name: SCHEMA optimisation; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA optimisation TO python;


--
-- Name: SCHEMA renewables; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA renewables TO python;


--
-- Name: SCHEMA tariffs; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA tariffs TO python;


--
-- Name: SCHEMA weather; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA weather TO python;


--
-- Name: TABLE grid_co2; Type: ACL; Schema: carbon_intensity; Owner: -
--

GRANT ALL ON TABLE carbon_intensity.grid_co2 TO python;


--
-- Name: TABLE metadata; Type: ACL; Schema: carbon_intensity; Owner: -
--

GRANT ALL ON TABLE carbon_intensity.metadata TO python;


--
-- Name: TABLE clients; Type: ACL; Schema: client_info; Owner: -
--

GRANT ALL ON TABLE client_info.clients TO python;


--
-- Name: TABLE site_info; Type: ACL; Schema: client_info; Owner: -
--

GRANT ALL ON TABLE client_info.site_info TO python;


--
-- Name: TABLE electricity_meters; Type: ACL; Schema: client_meters; Owner: -
--

GRANT ALL ON TABLE client_meters.electricity_meters TO python;


--
-- Name: TABLE electricity_meters_synthesised; Type: ACL; Schema: client_meters; Owner: -
--

GRANT ALL ON TABLE client_meters.electricity_meters_synthesised TO python;


--
-- Name: TABLE gas_meters; Type: ACL; Schema: client_meters; Owner: -
--

GRANT ALL ON TABLE client_meters.gas_meters TO python;


--
-- Name: TABLE metadata; Type: ACL; Schema: client_meters; Owner: -
--

GRANT ALL ON TABLE client_meters.metadata TO python;


--
-- Name: TABLE metadata; Type: ACL; Schema: heating; Owner: -
--

GRANT ALL ON TABLE heating.metadata TO python;


--
-- Name: TABLE synthesised; Type: ACL; Schema: heating; Owner: -
--

GRANT ALL ON TABLE heating.synthesised TO python;


--
-- Name: TABLE results; Type: ACL; Schema: optimisation; Owner: -
--

GRANT ALL ON TABLE optimisation.results TO python;


--
-- Name: TABLE task_config; Type: ACL; Schema: optimisation; Owner: -
--

GRANT ALL ON TABLE optimisation.task_config TO python;


--
-- Name: TABLE metadata; Type: ACL; Schema: renewables; Owner: -
--

GRANT ALL ON TABLE renewables.metadata TO python;


--
-- Name: TABLE metadata; Type: ACL; Schema: tariffs; Owner: -
--

GRANT ALL ON TABLE tariffs.metadata TO python;


--
-- Name: TABLE solar_pv; Type: ACL; Schema: renewables; Owner: -
--

GRANT ALL ON TABLE renewables.solar_pv TO python;


--
-- Name: TABLE electricity; Type: ACL; Schema: tariffs; Owner: -
--

GRANT ALL ON TABLE tariffs.electricity TO python;


--
-- Name: TABLE visual_crossing; Type: ACL; Schema: weather; Owner: -
--

GRANT ALL ON TABLE weather.visual_crossing TO python;


--
-- PostgreSQL database dump complete
--


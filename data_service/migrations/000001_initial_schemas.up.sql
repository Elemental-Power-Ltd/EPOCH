--
-- PostgreSQL database dump
--

-- Dumped from database version 14.13 (Ubuntu 14.13-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.13 (Ubuntu 14.13-0ubuntu0.22.04.1)


CREATE SCHEMA carbon_intensity;
CREATE SCHEMA client_info;
CREATE SCHEMA client_meters;
CREATE SCHEMA heating;
CREATE SCHEMA optimisation;
CREATE SCHEMA renewables;
CREATE SCHEMA tariffs;
CREATE SCHEMA weather;


CREATE TYPE public.latlon AS (
	lat double precision,
	lon double precision
);

CREATE TYPE public.objective_t AS (
	carbon_balance double precision,
	cost_balance double precision,
	capex double precision,
	payback_horizon double precision,
	annualised_cost double precision
);

CREATE TYPE public.stdortou AS ENUM (
    'Std',
    'ToU'
);

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


CREATE TABLE carbon_intensity.metadata (
    dataset_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    data_source text,
    is_regional boolean,
    site_id text,
    deleted_at timestamp with time zone
);


CREATE TABLE client_info.clients (
    client_id text NOT NULL,
    name text
);

CREATE TABLE client_info.site_info (
    site_id text NOT NULL,
    name text,
    address text,
    location text,
    coordinates public.latlon,
    client_id text
);


CREATE TABLE client_meters.electricity_meters (
    dataset_id uuid,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    consumption_kwh double precision,
    unit_cost numeric(19,4),
    total_cost numeric(19,4)
);


CREATE TABLE client_meters.electricity_meters_synthesised (
    dataset_id uuid,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    consumption_kwh double precision
);


CREATE TABLE client_meters.gas_meters (
    dataset_id uuid,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    consumption_kwh double precision,
    consumption_m3 double precision,
    unit_cost numeric(19,4),
    total_cost numeric(19,4)
);


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

CREATE TABLE heating.fabric_interventions (
    site_id text NOT NULL,
    intervention text NOT NULL,
    cost numeric(15,6)
);


CREATE TABLE heating.interventions (
    site_id text NOT NULL,
    intervention text NOT NULL,
    cost numeric(15,4)
);


CREATE TABLE heating.metadata (
    dataset_id uuid NOT NULL,
    site_id text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    params jsonb,
    interventions text[]
);


CREATE TABLE heating.synthesised (
    dataset_id uuid NOT NULL,
    start_ts timestamp with time zone NOT NULL,
    end_ts timestamp with time zone NOT NULL,
    heating double precision,
    dhw double precision,
    air_temperature double precision
);


CREATE TABLE optimisation.optimisers (
    name text NOT NULL
);


CREATE TABLE optimisation.results (
    task_id uuid,
    site_id text,
    solutions jsonb NOT NULL,
    objective_values public.objective_t NOT NULL,
    n_evals integer,
    exec_time interval,
    completed_at timestamp with time zone DEFAULT now() NOT NULL,
    results_id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    CONSTRAINT results_n_evals_check CHECK ((n_evals > 0))
);


CREATE TABLE optimisation.task_config (
    task_id uuid NOT NULL,
    task_name text,
    client_id text,
    objective_directions public.objective_t NOT NULL,
    constraints_min public.objective_t,
    constraints_max public.objective_t,
    parameters jsonb,
    input_data jsonb,
    optimiser_type text NOT NULL,
    optimiser_hyperparameters jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


CREATE TABLE renewables.metadata (
    dataset_id uuid NOT NULL,
    site_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    data_source text,
    parameters jsonb
);


CREATE TABLE renewables.solar_pv (
    dataset_id uuid,
    "timestamp" timestamp with time zone NOT NULL,
    solar_generation double precision NOT NULL
);


CREATE TABLE tariffs.electricity (
    dataset_id uuid,
    "timestamp" timestamp with time zone NOT NULL,
    unit_cost numeric(15,4),
    flat_cost numeric(15,5)
);


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


ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_0 FOR VALUES WITH (modulus 8, remainder 0);
ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_1 FOR VALUES WITH (modulus 8, remainder 1);
ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_2 FOR VALUES WITH (modulus 8, remainder 2);
ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_3 FOR VALUES WITH (modulus 8, remainder 3);
ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_4 FOR VALUES WITH (modulus 8, remainder 4);
ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_5 FOR VALUES WITH (modulus 8, remainder 5);
ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_6 FOR VALUES WITH (modulus 8, remainder 6);
ALTER TABLE ONLY weather.visual_crossing ATTACH PARTITION weather.visual_crossing_part_7 FOR VALUES WITH (modulus 8, remainder 7);
ALTER TABLE ONLY carbon_intensity.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);


ALTER TABLE ONLY client_info.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (client_id);

ALTER TABLE ONLY client_info.site_info
    ADD CONSTRAINT site_info_pkey PRIMARY KEY (site_id);

ALTER TABLE ONLY client_meters.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);

ALTER TABLE ONLY heating.fabric_interventions
    ADD CONSTRAINT fabric_interventions_pkey PRIMARY KEY (site_id, intervention);

ALTER TABLE ONLY heating.interventions
    ADD CONSTRAINT interventions_pkey PRIMARY KEY (site_id, intervention);

ALTER TABLE ONLY heating.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);

ALTER TABLE ONLY optimisation.task_config
    ADD CONSTRAINT job_config_pkey PRIMARY KEY (task_id);

ALTER TABLE ONLY optimisation.optimisers
    ADD CONSTRAINT optimisers_pkey PRIMARY KEY (name);

ALTER TABLE ONLY renewables.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);

ALTER TABLE ONLY tariffs.metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (dataset_id);


CREATE INDEX electricity_meters_idx ON client_meters.electricity_meters USING btree (dataset_id, start_ts);
CREATE INDEX gas_meters_idx ON client_meters.gas_meters USING btree (dataset_id, start_ts);


CREATE UNIQUE INDEX visual_crossing_loc_timestamp ON ONLY weather.visual_crossing USING btree (location, "timestamp");


CREATE UNIQUE INDEX visual_crossing_part_0_location_timestamp_idx ON weather.visual_crossing_part_0 USING btree (location, "timestamp");
CREATE UNIQUE INDEX visual_crossing_part_1_location_timestamp_idx ON weather.visual_crossing_part_1 USING btree (location, "timestamp");
CREATE UNIQUE INDEX visual_crossing_part_2_location_timestamp_idx ON weather.visual_crossing_part_2 USING btree (location, "timestamp");
CREATE UNIQUE INDEX visual_crossing_part_3_location_timestamp_idx ON weather.visual_crossing_part_3 USING btree (location, "timestamp");
CREATE UNIQUE INDEX visual_crossing_part_4_location_timestamp_idx ON weather.visual_crossing_part_4 USING btree (location, "timestamp");
CREATE UNIQUE INDEX visual_crossing_part_5_location_timestamp_idx ON weather.visual_crossing_part_5 USING btree (location, "timestamp");
CREATE UNIQUE INDEX visual_crossing_part_6_location_timestamp_idx ON weather.visual_crossing_part_6 USING btree (location, "timestamp");
CREATE UNIQUE INDEX visual_crossing_part_7_location_timestamp_idx ON weather.visual_crossing_part_7 USING btree (location, "timestamp");

ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_0_location_timestamp_idx;
ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_1_location_timestamp_idx;
ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_2_location_timestamp_idx;
ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_3_location_timestamp_idx;
ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_4_location_timestamp_idx;
ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_5_location_timestamp_idx;
ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_6_location_timestamp_idx;
ALTER INDEX weather.visual_crossing_loc_timestamp ATTACH PARTITION weather.visual_crossing_part_7_location_timestamp_idx;

ALTER TABLE ONLY carbon_intensity.grid_co2
    ADD CONSTRAINT grid_co2_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES carbon_intensity.metadata(dataset_id);

ALTER TABLE ONLY carbon_intensity.metadata
    ADD CONSTRAINT metadata_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id) DEFERRABLE;


ALTER TABLE ONLY client_info.site_info
    ADD CONSTRAINT site_info_client_id_fkey FOREIGN KEY (client_id) REFERENCES client_info.clients(client_id);


ALTER TABLE ONLY client_meters.electricity_meters
    ADD CONSTRAINT electricity_meters_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES client_meters.metadata(dataset_id);


ALTER TABLE ONLY client_meters.electricity_meters_synthesised
    ADD CONSTRAINT electricity_meters_synthesised_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES client_meters.metadata(dataset_id);


ALTER TABLE ONLY client_meters.metadata
    ADD CONSTRAINT fk_metadata_site_id FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


ALTER TABLE ONLY client_meters.gas_meters
    ADD CONSTRAINT gas_meters_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES client_meters.metadata(dataset_id);


ALTER TABLE ONLY heating.fabric_interventions
    ADD CONSTRAINT fabric_interventions_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


ALTER TABLE ONLY heating.interventions
    ADD CONSTRAINT interventions_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


ALTER TABLE ONLY heating.metadata
    ADD CONSTRAINT metadata_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


ALTER TABLE ONLY heating.synthesised
    ADD CONSTRAINT synthesised_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES heating.metadata(dataset_id) DEFERRABLE;


ALTER TABLE ONLY optimisation.task_config
    ADD CONSTRAINT fk_job_config_optimiser_type_optimiser_name FOREIGN KEY (optimiser_type) REFERENCES optimisation.optimisers(name);


ALTER TABLE ONLY optimisation.results
    ADD CONSTRAINT results_id_fkey FOREIGN KEY (task_id) REFERENCES optimisation.task_config(task_id);


ALTER TABLE ONLY renewables.metadata
    ADD CONSTRAINT metadata_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


ALTER TABLE ONLY renewables.solar_pv
    ADD CONSTRAINT solar_pv_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES renewables.metadata(dataset_id);


ALTER TABLE ONLY tariffs.electricity
    ADD CONSTRAINT electricity_dataset_id_metadata_fkey FOREIGN KEY (dataset_id) REFERENCES tariffs.metadata(dataset_id) DEFERRABLE INITIALLY DEFERRED;


ALTER TABLE ONLY tariffs.metadata
    ADD CONSTRAINT metadata_site_id_fkey FOREIGN KEY (site_id) REFERENCES client_info.site_info(site_id);


GRANT ALL ON SCHEMA carbon_intensity TO python;
GRANT ALL ON SCHEMA client_info TO python;
GRANT ALL ON SCHEMA client_meters TO python;
GRANT ALL ON SCHEMA heating TO python;
GRANT ALL ON SCHEMA optimisation TO python;
GRANT ALL ON SCHEMA renewables TO python;
GRANT ALL ON SCHEMA tariffs TO python;
GRANT ALL ON SCHEMA weather TO python;
GRANT ALL ON TABLE carbon_intensity.grid_co2 TO python;
GRANT ALL ON TABLE carbon_intensity.metadata TO python;
GRANT ALL ON TABLE client_info.clients TO python;
GRANT ALL ON TABLE client_info.site_info TO python;
GRANT ALL ON TABLE client_meters.electricity_meters TO python;
GRANT ALL ON TABLE client_meters.electricity_meters_synthesised TO python;
GRANT ALL ON TABLE client_meters.gas_meters TO python;
GRANT ALL ON TABLE client_meters.metadata TO python;
GRANT ALL ON TABLE heating.metadata TO python;
GRANT ALL ON TABLE heating.synthesised TO python;
GRANT ALL ON TABLE optimisation.results TO python;
GRANT ALL ON TABLE optimisation.task_config TO python;
GRANT ALL ON TABLE renewables.metadata TO python;
GRANT ALL ON TABLE renewables.solar_pv TO python;
GRANT ALL ON TABLE tariffs.electricity TO python;
GRANT ALL ON TABLE tariffs.metadata TO python;
GRANT ALL ON TABLE weather.visual_crossing TO python;
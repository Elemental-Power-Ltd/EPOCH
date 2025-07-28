BEGIN;
-- Create some indexes to make the slowest tables in production much nicer.
-- Note that we don't do these CONCURRENTLY so you'll lock the tables for a bit.
-- This is faster but you should do it when the DB isn't in use.

-- These are the slowest tables; they contain a mixture of UUIDv7 and UUIDv4s in their dataset_id columns
-- which is frustrating but inevitable. 
-- We'd love to use a hash index or a BRIN, but the btree is the best choice for now.
-- In future, it might be worth including some extra columns in here 
CREATE INDEX heating_synthesised_dataset_id_idx ON heating.synthesised USING btree (dataset_id);
CREATE INDEX tariffs_electricity_dataset_id_idx ON tariffs.electricity USING btree (dataset_id);
CREATE INDEX carbon_intensity_grid_co2_dataset_id_idx ON carbon_intensity.grid_co2 USING btree (dataset_id);
CREATE INDEX client_meters_electricity_meters_synthesised_dataset_id_idx
ON client_meters.electricity_meters_synthesised USING btree (dataset_id);
CREATE INDEX renewables_solar_pv_dataset_id_idx ON renewables.solar_pv USING btree (dataset_id);

-- These tables are tiny but frequently hit, and we expect them to get bigger.
CREATE INDEX heating_metadata_site_id_idx ON heating.metadata USING btree (site_id) INCLUDE (dataset_id);
CREATE INDEX tariffs_metadata_site_id_idx ON tariffs.metadata USING btree (site_id) INCLUDE (dataset_id);
CREATE INDEX carbon_intensity_metadata_site_id_idx ON carbon_intensity.metadata USING btree (site_id) INCLUDE (dataset_id);
CREATE INDEX client_meters_metadata_site_id_idx ON client_meters.metadata USING btree (site_id) INCLUDE (dataset_id);
CREATE INDEX renewables_metadata_site_id_idx ON renewables.metadata USING btree (site_id) INCLUDE (dataset_id);

END;

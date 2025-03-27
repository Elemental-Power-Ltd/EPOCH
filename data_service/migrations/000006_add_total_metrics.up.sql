BEGIN;

ALTER TABLE optimisation.portfolio_results
    ADD COLUMN metric_total_gas_used double precision,
    ADD COLUMN metric_total_electricity_imported double precision,
    ADD COLUMN metric_total_electricity_generated double precision,
    ADD COLUMN metric_total_electricity_exported double precision,
    ADD COLUMN metric_total_electrical_shortfall double precision,
    ADD COLUMN metric_total_heat_shortfall double precision,
    ADD COLUMN metric_total_gas_import_cost double precision,
    ADD COLUMN metric_total_electricity_import_cost double precision,
    ADD COLUMN metric_total_electricity_export_gain double precision;

ALTER TABLE optimisation.site_results
    ADD COLUMN metric_total_gas_used double precision,
    ADD COLUMN metric_total_electricity_imported double precision,
    ADD COLUMN metric_total_electricity_generated double precision,
    ADD COLUMN metric_total_electricity_exported double precision,
    ADD COLUMN metric_total_electrical_shortfall double precision,
    ADD COLUMN metric_total_heat_shortfall double precision,
    ADD COLUMN metric_total_gas_import_cost double precision,
    ADD COLUMN metric_total_electricity_import_cost double precision,
    ADD COLUMN metric_total_electricity_export_gain double precision;

END;
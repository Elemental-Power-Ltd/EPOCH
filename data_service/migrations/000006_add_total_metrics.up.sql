BEGIN;

ALTER TABLE optimisation.portfolio_results
ADD COLUMN metric_total_gas_used DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_imported DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_generated DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_exported DOUBLE PRECISION,
ADD COLUMN metric_total_electrical_shortfall DOUBLE PRECISION,
ADD COLUMN metric_total_heat_shortfall DOUBLE PRECISION,
ADD COLUMN metric_total_gas_import_cost DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_import_cost DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_export_gain DOUBLE PRECISION;

ALTER TABLE optimisation.site_results
ADD COLUMN metric_total_gas_used DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_imported DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_generated DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_exported DOUBLE PRECISION,
ADD COLUMN metric_total_electrical_shortfall DOUBLE PRECISION,
ADD COLUMN metric_total_heat_shortfall DOUBLE PRECISION,
ADD COLUMN metric_total_gas_import_cost DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_import_cost DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_export_gain DOUBLE PRECISION;

END;

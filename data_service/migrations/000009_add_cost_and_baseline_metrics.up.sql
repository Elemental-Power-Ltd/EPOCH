BEGIN;

ALTER TABLE optimisation.portfolio_results
ADD COLUMN metric_meter_balance DOUBLE PRECISION,
ADD COLUMN metric_operating_balance DOUBLE PRECISION,
ADD COLUMN metric_total_meter_cost DOUBLE PRECISION,
ADD COLUMN metric_baseline_gas_used DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_imported DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_generated DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_exported DOUBLE PRECISION,
ADD COLUMN metric_baseline_electrical_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_heat_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_gas_import_cost DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_import_cost DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_export_gain DOUBLE PRECISION,
ADD COLUMN metric_baseline_meter_cost DOUBLE PRECISION;

ALTER TABLE optimisation.site_results
ADD COLUMN metric_meter_balance DOUBLE PRECISION,
ADD COLUMN metric_operating_balance DOUBLE PRECISION,
ADD COLUMN metric_total_meter_cost DOUBLE PRECISION,
ADD COLUMN metric_baseline_gas_used DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_imported DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_generated DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_exported DOUBLE PRECISION,
ADD COLUMN metric_baseline_electrical_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_heat_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_gas_import_cost DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_import_cost DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_export_gain DOUBLE PRECISION,
ADD COLUMN metric_baseline_meter_cost DOUBLE PRECISION;

END;

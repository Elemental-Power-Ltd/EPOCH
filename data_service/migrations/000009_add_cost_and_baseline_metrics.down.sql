BEGIN;

ALTER TABLE optimisation.portfolio_results
DROP COLUMN IF EXISTS metric_meter_balance,
DROP COLUMN IF EXISTS metric_operating_balance,
DROP COLUMN IF EXISTS metric_total_meter_cost,
DROP COLUMN IF EXISTS metric_baseline_gas_used,
DROP COLUMN IF EXISTS metric_baseline_electricity_imported,
DROP COLUMN IF EXISTS metric_baseline_electricity_generated,
DROP COLUMN IF EXISTS metric_baseline_electricity_exported,
DROP COLUMN IF EXISTS metric_baseline_electrical_shortfall,
DROP COLUMN IF EXISTS metric_baseline_heat_shortfall,
DROP COLUMN IF EXISTS metric_baseline_gas_import_cost,
DROP COLUMN IF EXISTS metric_baseline_electricity_import_cost,
DROP COLUMN IF EXISTS metric_baseline_electricity_export_gain,
DROP COLUMN IF EXISTS metric_baseline_meter_cost;


ALTER TABLE optimisation.site_results
DROP COLUMN IF EXISTS metric_meter_balance,
DROP COLUMN IF EXISTS metric_operating_balance,
DROP COLUMN IF EXISTS metric_total_meter_cost,
DROP COLUMN IF EXISTS metric_baseline_gas_used,
DROP COLUMN IF EXISTS metric_baseline_electricity_imported,
DROP COLUMN IF EXISTS metric_baseline_electricity_generated,
DROP COLUMN IF EXISTS metric_baseline_electricity_exported,
DROP COLUMN IF EXISTS metric_baseline_electrical_shortfall,
DROP COLUMN IF EXISTS metric_baseline_heat_shortfall,
DROP COLUMN IF EXISTS metric_baseline_gas_import_cost,
DROP COLUMN IF EXISTS metric_baseline_electricity_import_cost,
DROP COLUMN IF EXISTS metric_baseline_electricity_export_gain,
DROP COLUMN IF EXISTS metric_baseline_meter_cost;

END;

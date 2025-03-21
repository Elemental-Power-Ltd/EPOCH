BEGIN;

ALTER TABLE optimisation.portfolio_results
    DROP COLUMN IF EXISTS metric_total_gas_used,
    DROP COLUMN IF EXISTS metric_total_electricity_imported,
    DROP COLUMN IF EXISTS metric_total_electricity_generated,
    DROP COLUMN IF EXISTS metric_total_electricity_exported,
    DROP COLUMN IF EXISTS metric_total_electrical_shortfall,
    DROP COLUMN IF EXISTS metric_total_heat_shortfall,
    DROP COLUMN IF EXISTS metric_total_gas_import_cost,
    DROP COLUMN IF EXISTS metric_total_electricity_import_cost,
    DROP COLUMN IF EXISTS metric_total_electricity_export_gain;

ALTER TABLE optimisation.site_results
    DROP COLUMN IF EXISTS metric_total_gas_used,
    DROP COLUMN IF EXISTS metric_total_electricity_imported,
    DROP COLUMN IF EXISTS metric_total_electricity_generated,
    DROP COLUMN IF EXISTS metric_total_electricity_exported,
    DROP COLUMN IF EXISTS metric_total_electrical_shortfall,
    DROP COLUMN IF EXISTS metric_total_heat_shortfall,
    DROP COLUMN IF EXISTS metric_total_gas_import_cost,
    DROP COLUMN IF EXISTS metric_total_electricity_import_cost,
    DROP COLUMN IF EXISTS metric_total_electricity_export_gain;

END;
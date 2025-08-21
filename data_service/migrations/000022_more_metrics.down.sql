BEGIN;

ALTER TABLE optimisation.portfolio_results
DROP COLUMN IF EXISTS metric_total_electricity_used,
DROP COLUMN IF EXISTS metric_total_electricity_curtailed,
DROP COLUMN IF EXISTS metric_total_scope_1_emissions,
DROP COLUMN IF EXISTS metric_total_scope_2_emissions,
DROP COLUMN IF EXISTS metric_total_combined_carbon_emissions,
DROP COLUMN IF EXISTS metric_combined_carbon_balance,

DROP COLUMN IF EXISTS metric_baseline_electricity_used,
DROP COLUMN IF EXISTS metric_baseline_electricity_curtailed,
DROP COLUMN IF EXISTS metric_baseline_scope_1_emissions,
DROP COLUMN IF EXISTS metric_baseline_scope_2_emissions,
DROP COLUMN IF EXISTS metric_baseline_combined_carbon_emissions;

ALTER TABLE optimisation.site_results

DROP COLUMN IF EXISTS metric_total_electricity_used,
DROP COLUMN IF EXISTS metric_total_electricity_curtailed,
DROP COLUMN IF EXISTS metric_total_scope_1_emissions,
DROP COLUMN IF EXISTS metric_total_scope_2_emissions,
DROP COLUMN IF EXISTS metric_total_combined_carbon_emissions,
DROP COLUMN IF EXISTS metric_combined_carbon_balance,
DROP COLUMN IF EXISTS metric_scenario_environmental_impact_score,
DROP COLUMN IF EXISTS metric_scenario_environmental_impact_grade,

DROP COLUMN IF EXISTS metric_baseline_electricity_used,
DROP COLUMN IF EXISTS metric_baseline_electricity_curtailed,
DROP COLUMN IF EXISTS metric_baseline_scope_1_emissions,
DROP COLUMN IF EXISTS metric_baseline_scope_2_emissions,
DROP COLUMN IF EXISTS metric_baseline_combined_carbon_emissions,
DROP COLUMN IF EXISTS metric_baseline_environmental_impact_score,
DROP COLUMN IF EXISTS metric_baseline_environmental_impact_grade;

DROP TYPE IF EXISTS GRADE_ENUM;

END;

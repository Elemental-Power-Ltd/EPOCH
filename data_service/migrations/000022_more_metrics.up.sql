BEGIN;

CREATE TYPE "GRADE_ENUM" AS ENUM ('A', 'B', 'C', 'D', 'E', 'F', 'G');

ALTER TABLE optimisation.portfolio_results
ADD COLUMN metric_total_electricity_used DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_curtailed DOUBLE PRECISION,
ADD COLUMN metric_total_scope_1_emissions DOUBLE PRECISION,
ADD COLUMN metric_total_scope_2_emissions DOUBLE PRECISION,
ADD COLUMN metric_total_combined_carbon_emissions DOUBLE PRECISION,
ADD COLUMN metric_combined_carbon_balance DOUBLE PRECISION,

ADD COLUMN metric_baseline_electricity_used DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_curtailed DOUBLE PRECISION,
ADD COLUMN metric_baseline_scope_1_emissions DOUBLE PRECISION,
ADD COLUMN metric_baseline_scope_2_emissions DOUBLE PRECISION,
ADD COLUMN metric_baseline_combined_carbon_emissions DOUBLE PRECISION;

ALTER TABLE optimisation.site_results

ADD COLUMN metric_total_electricity_used DOUBLE PRECISION,
ADD COLUMN metric_total_electricity_curtailed DOUBLE PRECISION,
ADD COLUMN metric_total_scope_1_emissions DOUBLE PRECISION,
ADD COLUMN metric_total_scope_2_emissions DOUBLE PRECISION,
ADD COLUMN metric_total_combined_carbon_emissions DOUBLE PRECISION,
ADD COLUMN metric_combined_carbon_balance DOUBLE PRECISION,
ADD COLUMN metric_scenario_environmental_impact_score DOUBLE PRECISION,
ADD COLUMN metric_scenario_environmental_impact_grade "GRADE_ENUM",

ADD COLUMN metric_baseline_electricity_used DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_curtailed DOUBLE PRECISION,
ADD COLUMN metric_baseline_scope_1_emissions DOUBLE PRECISION,
ADD COLUMN metric_baseline_scope_2_emissions DOUBLE PRECISION,
ADD COLUMN metric_baseline_combined_carbon_emissions DOUBLE PRECISION,
ADD COLUMN metric_baseline_environmental_impact_score DOUBLE PRECISION,
ADD COLUMN metric_baseline_environmental_impact_grade "GRADE_ENUM";

END;

BEGIN;

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

ADD COLUMN metric_baseline_electricity_used DOUBLE PRECISION,
ADD COLUMN metric_baseline_electricity_curtailed DOUBLE PRECISION,
ADD COLUMN metric_baseline_scope_1_emissions DOUBLE PRECISION,
ADD COLUMN metric_baseline_scope_2_emissions DOUBLE PRECISION,
ADD COLUMN metric_baseline_combined_carbon_emissions DOUBLE PRECISION;

END;

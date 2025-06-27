BEGIN;

ALTER TABLE optimisation.portfolio_results
ADD COLUMN metric_total_operating_cost DOUBLE PRECISION,
ADD COLUMN metric_baseline_operating_cost DOUBLE PRECISION,
ADD COLUMN metric_total_net_present_value DOUBLE PRECISION,
ADD COLUMN metric_baseline_net_present_value DOUBLE PRECISION,
ADD COLUMN metric_npv_balance DOUBLE PRECISION;


ALTER TABLE optimisation.site_results
ADD COLUMN metric_total_operating_cost DOUBLE PRECISION,
ADD COLUMN metric_baseline_operating_cost DOUBLE PRECISION,
ADD COLUMN metric_total_net_present_value DOUBLE PRECISION,
ADD COLUMN metric_baseline_net_present_value DOUBLE PRECISION,
ADD COLUMN metric_npv_balance DOUBLE PRECISION;

END;

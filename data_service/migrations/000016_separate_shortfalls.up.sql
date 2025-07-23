BEGIN;

ALTER TABLE optimisation.portfolio_results
ADD COLUMN metric_total_ch_shortfall DOUBLE PRECISION,
ADD COLUMN metric_total_dhw_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_ch_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_dhw_shortfall DOUBLE PRECISION;

ALTER TABLE optimisation.site_results
ADD COLUMN metric_total_ch_shortfall DOUBLE PRECISION,
ADD COLUMN metric_total_dhw_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_ch_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_dhw_shortfall DOUBLE PRECISION;

END;

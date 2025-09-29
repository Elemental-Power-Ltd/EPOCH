BEGIN;

ALTER TABLE optimisation.portfolio_results
ADD COLUMN metric_peak_hload_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_peak_hload_shortfall DOUBLE PRECISION;

ALTER TABLE optimisation.site_results
ADD COLUMN metric_peak_hload_shortfall DOUBLE PRECISION,
ADD COLUMN metric_baseline_peak_hload_shortfall DOUBLE PRECISION;

END;

BEGIN;

ALTER TABLE optimisation.portfolio_results
DROP COLUMN metric_peak_hload_shortfall,
DROP COLUMN metric_baseline_peak_hload_shortfall;

ALTER TABLE optimisation.site_results
DROP COLUMN metric_peak_hload_shortfall,
DROP COLUMN metric_baseline_peak_hload_shortfall;

END;

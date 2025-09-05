BEGIN;

ALTER TABLE optimisation.portfolio_results
DROP COLUMN metric_total_heat_load,
DROP COLUMN metric_total_dhw_load,
DROP COLUMN metric_total_ch_load,
DROP COLUMN metric_baseline_heat_load,
DROP COLUMN metric_baseline_dhw_load,
DROP COLUMN metric_baseline_ch_load;

ALTER TABLE optimisation.site_results

DROP COLUMN metric_total_heat_load,
DROP COLUMN metric_total_dhw_load,
DROP COLUMN metric_total_ch_load,
DROP COLUMN metric_baseline_heat_load,
DROP COLUMN metric_baseline_dhw_load,
DROP COLUMN metric_baseline_ch_load;

END;

BEGIN;

ALTER TABLE optimisation.portfolio_results
ADD COLUMN metric_total_heat_load DOUBLE PRECISION,
ADD COLUMN metric_total_dhw_load DOUBLE PRECISION,
ADD COLUMN metric_total_ch_load DOUBLE PRECISION,
ADD COLUMN metric_baseline_heat_load DOUBLE PRECISION,
ADD COLUMN metric_baseline_dhw_load DOUBLE PRECISION,
ADD COLUMN metric_baseline_ch_load DOUBLE PRECISION;

ALTER TABLE optimisation.site_results

ADD COLUMN metric_total_heat_load DOUBLE PRECISION,
ADD COLUMN metric_total_dhw_load DOUBLE PRECISION,
ADD COLUMN metric_total_ch_load DOUBLE PRECISION,
ADD COLUMN metric_baseline_heat_load DOUBLE PRECISION,
ADD COLUMN metric_baseline_dhw_load DOUBLE PRECISION,
ADD COLUMN metric_baseline_ch_load DOUBLE PRECISION;

END;

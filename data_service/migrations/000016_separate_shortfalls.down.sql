BEGIN;

ALTER TABLE optimisation.portfolio_results
DROP COLUMN IF EXISTS metric_total_ch_shortfall,
DROP COLUMN IF EXISTS metric_total_dhw_shortfall,
DROP COLUMN IF EXISTS metric_baseline_ch_shortfall,
DROP COLUMN IF EXISTS metric_baseline_dhw_shortfall;

ALTER TABLE optimisation.site_results
DROP COLUMN IF EXISTS metric_total_ch_shortfall,
DROP COLUMN IF EXISTS metric_total_dhw_shortfall,
DROP COLUMN IF EXISTS metric_baseline_ch_shortfall,
DROP COLUMN IF EXISTS metric_baseline_dhw_shortfall;

END;

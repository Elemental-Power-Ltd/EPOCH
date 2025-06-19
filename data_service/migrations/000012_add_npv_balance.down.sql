BEGIN;

ALTER TABLE optimisation.portfolio_results
DROP COLUMN IF EXISTS metric_total_operating_cost,
DROP COLUMN IF EXISTS metric_baseline_operating_cost,
DROP COLUMN IF EXISTS metric_total_net_present_value,
DROP COLUMN IF EXISTS metric_baseline_net_present_value,
DROP COLUMN IF EXISTS metric_npv_balance;


ALTER TABLE optimisation.site_results
DROP COLUMN IF EXISTS metric_total_operating_cost,
DROP COLUMN IF EXISTS metric_baseline_operating_cost,
DROP COLUMN IF EXISTS metric_total_net_present_value,
DROP COLUMN IF EXISTS metric_baseline_net_present_value,
DROP COLUMN IF EXISTS metric_npv_balance;

END;

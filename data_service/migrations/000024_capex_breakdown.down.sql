BEGIN;

ALTER TABLE optimisation.site_results DROP COLUMN IF EXISTS scenario_capex_breakdown;

END;

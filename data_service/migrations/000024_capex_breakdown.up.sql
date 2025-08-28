BEGIN;

ALTER TABLE optimisation.site_results ADD COLUMN scenario_capex_breakdown JSONB;

END;

BEGIN;

ALTER TABLE optimisation.portfolio_results ADD COLUMN is_feasible BOOLEAN;

ALTER TABLE optimisation.site_results ADD COLUMN is_feasible BOOLEAN;

END;

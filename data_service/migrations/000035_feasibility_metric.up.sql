BEGIN;

ALTER TABLE optimisation.portfolio_results ADD COLUMN is_feasible boolean;

ALTER TABLE optimisation.site_results ADD COLUMN is_feasible boolean;

END;
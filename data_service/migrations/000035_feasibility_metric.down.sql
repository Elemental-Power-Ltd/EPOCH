BEGIN;

ALTER TABLE optimisation.portfolio_results DROP COLUMN is_feasible;

ALTER TABLE optimisation.site_results DROP COLUMN is_feasible;

END;

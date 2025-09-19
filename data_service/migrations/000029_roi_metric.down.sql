BEGIN;

ALTER TABLE optimisation.portfolio_results DROP COLUMN metric_return_on_investment;

ALTER TABLE optimisation.site_results DROP COLUMN metric_return_on_investment;

END;

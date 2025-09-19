BEGIN;

ALTER TABLE optimisation.portfolio_results ADD COLUMN metric_return_on_investment DOUBLE PRECISION;

ALTER TABLE optimisation.site_results ADD COLUMN metric_return_on_investment DOUBLE PRECISION;

END;

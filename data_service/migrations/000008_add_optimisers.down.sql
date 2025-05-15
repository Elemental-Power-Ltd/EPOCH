BEGIN;

DELETE FROM optimisation.optimisers
WHERE name IN ('Bayesian', 'SeparatedNSGA2', 'SeparatedNSGA2xNSGA2');

END;

BEGIN;

DELETE FROM optimisation.optimisers WHERE name = 'Bayesian';
DELETE FROM optimisation.optimisers WHERE name = 'SeparatedNSGA2';
DELETE FROM optimisation.optimisers WHERE name = 'SeparatedNSGA2xNSGA2';

END;
BEGIN;

DELETE FROM optimisation.optimisers
WHERE name IN ('MergeOperator');

END;
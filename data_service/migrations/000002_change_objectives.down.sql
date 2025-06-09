BEGIN;

ALTER TYPE public.objective_t RENAME ATTRIBUTE carbon_balance_scope_1 TO carbon_balance CASCADE;
ALTER TYPE public.objective_t DROP ATTRIBUTE carbon_balance_scope_2 CASCADE;
ALTER TYPE public.objective_t DROP ATTRIBUTE carbon_cost CASCADE;

END;

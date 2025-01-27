BEGIN;

ALTER TYPE public.objective_t RENAME ATTRIBUTE carbon_balance TO carbon_balance_scope_1 CASCADE;
ALTER TYPE public.objective_t ADD ATTRIBUTE carbon_balance_scope_2 double precision CASCADE;
ALTER TYPE public.objective_t ADD ATTRIBUTE carbon_cost double precision CASCADE;


END;
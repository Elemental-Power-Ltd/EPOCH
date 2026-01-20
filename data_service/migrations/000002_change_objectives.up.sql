BEGIN;

ALTER TYPE public.objective_t RENAME ATTRIBUTE carbon_balance TO carbon_balance_scope_1 CASCADE; -- noqa: CP05
ALTER TYPE public.objective_t ADD ATTRIBUTE carbon_balance_scope_2 DOUBLE PRECISION CASCADE; -- noqa: CP05
ALTER TYPE public.objective_t ADD ATTRIBUTE carbon_cost DOUBLE PRECISION CASCADE; -- noqa: CP05

END;

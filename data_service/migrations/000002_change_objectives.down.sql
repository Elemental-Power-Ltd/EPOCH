BEGIN;

ALTER TYPE public.objective_t RENAME ATTRIBUTE carbon_balance_scope_1 TO carbon_balance CASCADE; -- noqa: CP05
ALTER TYPE public.objective_t DROP ATTRIBUTE carbon_balance_scope_2 CASCADE; -- noqa: CP05
ALTER TYPE public.objective_t DROP ATTRIBUTE carbon_cost CASCADE; -- noqa: CP05

END;

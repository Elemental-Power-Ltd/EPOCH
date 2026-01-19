BEGIN;

CREATE TYPE public.stdortou AS ENUM ( -- noqa: CP05
    'Std',
    'ToU'
);

CREATE TABLE optimisation.optimisers (
    name TEXT NOT NULL -- noqa: RF04
);

INSERT INTO optimisation.optimisers (name) VALUES ('GridSearch');
INSERT INTO optimisation.optimisers (name) VALUES ('NSGA2');
INSERT INTO optimisation.optimisers (name) VALUES ('GeneticAlgorithm');

ALTER TABLE ONLY optimisation.optimisers
ADD CONSTRAINT optimisers_pkey PRIMARY KEY (name);

ALTER TABLE ONLY optimisation.task_config
ADD CONSTRAINT fk_job_config_optimiser_type_optimiser_name
FOREIGN KEY (optimiser_type) REFERENCES optimisation.optimisers (name);

END;

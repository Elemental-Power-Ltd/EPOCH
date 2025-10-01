BEGIN;

CREATE TABLE heating.feasible_interventions (
    site_id TEXT REFERENCES client_info.site_info (site_id),
    intervention_name TEXT NOT NULL
);

CREATE INDEX heating_feasible_interventions_site_id_idx ON heating.feasible_interventions USING btree (site_id);

END;

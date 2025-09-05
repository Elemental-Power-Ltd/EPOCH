BEGIN;

ALTER TABLE heating.metadata DROP COLUMN peak_hload;

DROP TABLE heating.structure_elements;
DROP TABLE heating.structure_metadata;

END;

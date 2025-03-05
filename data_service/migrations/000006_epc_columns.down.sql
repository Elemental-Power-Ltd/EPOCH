BEGIN;

ALTER TABLE client_info.site_info DROP COLUMN epc_lmk;
ALTER TABLE client_info.site_info DROP COLUMN dec_lmk;

END;
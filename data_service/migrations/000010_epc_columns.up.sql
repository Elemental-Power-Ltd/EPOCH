BEGIN;

ALTER TABLE client_info.site_info ADD epc_lmk TEXT;
ALTER TABLE client_info.site_info ADD dec_lmk TEXT;

END;
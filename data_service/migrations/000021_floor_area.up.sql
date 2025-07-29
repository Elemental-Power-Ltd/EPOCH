BEGIN;
-- This is in m^2, and may differ to the floor area calculated in PHPPs
-- Use this floor area for official metrics like carbon intensity per floor area, or SAP rating.
ALTER TABLE client_info.site_info ADD COLUMN floor_area FLOAT;

-- For the sites that are definitely in the database (because they're in the initial schemas)
-- set the floor areas if we know them.
-- These were mostly looked up manually from EPCs.
-- NULL out the ones that we can't find
UPDATE client_info.site_info SET floor_area = 433.0 WHERE site_id = '100_102_bridge_street';
UPDATE client_info.site_info SET floor_area = NULL WHERE site_id = 'best_lab';
UPDATE client_info.site_info SET floor_area = 2374.2 WHERE site_id = 'bircotes_leisure_centre';
UPDATE client_info.site_info SET floor_area = 999.0 WHERE site_id = 'bridge_skills_hub';
UPDATE client_info.site_info SET floor_area = 1891.0 WHERE site_id = 'carlton_forest_house';
UPDATE client_info.site_info SET floor_area = 89.0 WHERE site_id = 'demo_london';
UPDATE client_info.site_info SET floor_area = 100.0 WHERE site_id = 'demo_cardiff';
UPDATE client_info.site_info SET floor_area = 2122.0 WHERE site_id = 'demo_edinburgh';
UPDATE client_info.site_info SET floor_area = 353.0 WHERE site_id = 'kilton_community_centre';
UPDATE client_info.site_info SET floor_area = NULL WHERE site_id = 'corffe_house';
UPDATE client_info.site_info SET floor_area = 4418.0 WHERE site_id = 'queens_buildings';
UPDATE client_info.site_info SET floor_area = 2525.965 WHERE site_id = 'retford_leisure_centre';
UPDATE client_info.site_info SET floor_area = 1359.67 WHERE site_id = 'retford_town_hall';
UPDATE client_info.site_info SET floor_area = 2563.7 WHERE site_id = 'worksop_leisure_centre';
UPDATE client_info.site_info SET floor_area = 1649.6 WHERE site_id = 'worksop_town_hall';
UPDATE client_info.site_info SET floor_area = 540.0 WHERE site_id = 'amcott_house';
UPDATE client_info.site_info SET floor_area = 1359.67 WHERE site_id = 'retford_town_hall_house';

END;

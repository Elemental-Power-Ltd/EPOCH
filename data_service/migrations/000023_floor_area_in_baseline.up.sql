BEGIN;

-- For the existing baselines that don't have a floor area stored,
-- use the data from the site_info column (if it exists)
-- reject anything that doesn't have a building or already has a floor area
UPDATE client_info.site_baselines AS sb -- noqa: PRS
SET baseline['building']['floor_area'] = to_jsonb(si.floor_area)
FROM client_info.site_info AS si 
WHERE si.site_id = sb.site_id
AND sb.baseline ? 'building' AND NOT sb.baseline['building'] ? 'floor_area' 
AND si.floor_area IS NOT NULL;

ALTER TABLE client_info.site_info DROP COLUMN floor_area;

END;

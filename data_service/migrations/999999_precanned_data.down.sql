-- This file is set to the highest migration number so it isn't included in tests, and 
-- is applied after all the others.

BEGIN;

DELETE FROM client_info.site_baselines WHERE baseline_id in ('019c4cab-6f84-701c-b97f-f799c8b454f5''019c4cab-9f3f-71dd-842b-435279f806b8','019c4cab-bbec-7556-87f3-f6a94e789de0')
;

DELETE FROM client_info.solar_locations WHERE renewables_location_id (
    'demo_cardiff_mainarray_northeast'
    'demo_cardiff_mainarray_west', 
    'demo_cardiff_office',  
    'demo_cardiff_mainroof',
    'demo_london_west',
    'demo_london_east', 
    'demo_edinburgh_flat_east', 
    'demo_edinburgh_flat_west');

DELETE FROM client_meters.metadata WHERE dataset_id IN ('019c4cab-e8b6-7003-a22f-c7a82234b27d',
        '019c4cab-f9fd-7463-953f-1ab5e390c9cc',
        '019c4cac-9c36-7fc9-8895-076b1753a52f',
        '019c4cac-af70-775b-91ec-55bc32c23a21', 
        '019c4cac-c08f-7d76-bce8-bb5f3414dc89', 
        '019c4cac-d39e-7954-a9a0-6522b35975cc');

DELETE FROM client_meters.electricity_meters WHERE dataset_id IN ('019c4cab-e8b6-7003-a22f-c7a82234b27d',
        '019c4cab-f9fd-7463-953f-1ab5e390c9cc',
        '019c4cac-9c36-7fc9-8895-076b1753a52f',
        '019c4cac-af70-775b-91ec-55bc32c23a21', 
        '019c4cac-c08f-7d76-bce8-bb5f3414dc89', 
        '019c4cac-d39e-7954-a9a0-6522b35975cc');

DELETE FROM client_meters.gas_meters WHERE dataset_id IN ('019c4cab-e8b6-7003-a22f-c7a82234b27d',
        '019c4cab-f9fd-7463-953f-1ab5e390c9cc',
        '019c4cac-9c36-7fc9-8895-076b1753a52f',
        '019c4cac-af70-775b-91ec-55bc32c23a21', 
        '019c4cac-c08f-7d76-bce8-bb5f3414dc89', 
        '019c4cac-d39e-7954-a9a0-6522b35975cc');

END;
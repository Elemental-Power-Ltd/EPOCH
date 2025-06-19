import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box
} from '@mui/material';

import {
  TaskData,
  Config,
  Building,
  DataCentre,
  DomesticHotWater,
  ElectricVehicles,
  EnergyStorageSystem,
  GasHeater,
  Grid as GridComponent,
  HeatPump,
  Mop,
  SolarPanel,
} from './TaskData';

import {formatField} from "../../util/displayFunctions.ts";

// Human-readable names for each "top-level" component
const componentNames: Record<keyof TaskData, string> = {
  config:                'Config',
  building:              'Building',
  data_centre:           'Data Centre',
  domestic_hot_water:    'Domestic Hot Water',
  electric_vehicles:     'Electric Vehicles',
  energy_storage_system: 'Energy Storage System',
  gas_heater:            'Gas Heater',
  grid:                  'Grid',
  heat_pump:             'Heat Pump',
  mop:                   'MOP',
  solar_panels:          'Solar Panels',
};


interface FieldInfo {
  label: string;
  unit?: string; // e.g. "kW", "°C", "£"
}

/**
 * Map from each component key to its fields.
 */
const fieldMappings: {
  config: Record<keyof Config, FieldInfo>;
  building: Record<keyof Building, FieldInfo>;
  data_centre: Record<keyof DataCentre, FieldInfo>;
  domestic_hot_water: Record<keyof DomesticHotWater, FieldInfo>;
  electric_vehicles: Record<keyof ElectricVehicles, FieldInfo>;
  energy_storage_system: Record<keyof EnergyStorageSystem, FieldInfo>;
  gas_heater: Record<keyof GasHeater, FieldInfo>;
  grid: Record<keyof GridComponent, FieldInfo>;
  heat_pump: Record<keyof HeatPump, FieldInfo>;
  mop: Record<keyof Mop, FieldInfo>;
  solar_panels: Record<keyof SolarPanel, FieldInfo>; // solar_panels is an array of SolarPanel
} = {
  config: {
    capex_limit: { label: 'CAPEX Limit', unit: '£' },
    use_boiler_upgrade_scheme: {label: 'Boiler Scheme'},
    general_grant_funding: {label: 'General Funding', unit: '£'}
  },
  building: {
    scalar_heat_load:          { label: 'Heat Load'},
    scalar_electrical_load:    { label: 'Electrical Load'},
    fabric_intervention_index: { label: 'Fabric Intervention Index' },
  },
  data_centre: {
    maximum_load: { label: 'Maximum Load', unit: 'kW' },
    hotroom_temp: { label: 'Hotroom Temperature', unit: '°C' },
  },
  domestic_hot_water: {
    cylinder_volume: { label: 'Cylinder Volume', unit: 'litres' },
  },
  electric_vehicles: {
    flexible_load_ratio:   { label: 'Flexible Load Ratio', unit: 'decimal %' },
    small_chargers:        { label: 'Small Chargers'},
    fast_chargers:         { label: 'Fast Chargers'},
    rapid_chargers:        { label: 'Rapid Chargers'},
    ultra_chargers:        { label: 'Ultra Chargers'},
    scalar_electrical_load:{ label: 'EV Load Scalar'},
  },
  energy_storage_system: {
    capacity:        { label: 'Battery Capacity', unit: 'kWh' },
    charge_power:    { label: 'Charge Power', unit: 'kW' },
    discharge_power: { label: 'Discharge Power', unit: 'kW' },
    battery_mode:    { label: 'Battery Mode' },
    initial_charge:  { label: 'Initial Charge', unit: 'kWh' },
  },
  gas_heater: {
    maximum_output:    { label: 'Maximum Output', unit: 'kW' },
    gas_type:          { label: 'Gas Type' },
    boiler_efficiency: { label: 'Boiler Efficiency', unit: 'decimal %'},
  },
  grid: {
    grid_export:     { label: 'Grid Export', unit: 'kW' },
    grid_import:     { label: 'Grid Import', unit: 'kW' },
    import_headroom: { label: 'Import Headroom', unit: 'decimal %'},
    tariff_index:    { label: 'Tariff Index' },
    export_tariff: { label: 'Export Tariff', unit: '£/kWh' }
  },
  heat_pump: {
    heat_power: { label: 'Heat Power', unit: 'kW' },
    heat_source:{ label: 'Heat Source' },
    send_temp:  { label: 'Flow Temperature', unit: '°C' },
  },
  mop: {
    maximum_load: { label: 'Maximum Load', unit: 'kW' },
  },
  solar_panels: {
    yield_scalar: { label: 'Yield Scalar', unit: 'kW' },
    yield_index: {label: 'Yield Index'},
  },
};




/**
 * A small helper Card for displaying a single component (like Building or Grid)
 * in a single-column layout.
 */
const ComponentDetails: React.FC<{
  componentKey: keyof TaskData;
  componentData: any;
  titleOverride?: string; // solar_panels may supply a numbered title
}> = ({ componentKey, componentData, titleOverride }) => {
  const fieldsDef = fieldMappings[componentKey];
  if (!fieldsDef) return null;

  return (
    <Card
      variant="outlined"
      sx={{
        minWidth: 250,
        flex: '0 0 auto', // ensures the card won't shrink; allows horizontal scroll
        marginRight: 2,
      }}
    >
      <CardContent>
        <Typography
          variant="subtitle1"
          gutterBottom
          sx={{
            textAlign: 'center',
            fontWeight: 'bold',
          }}
        >
          {titleOverride ?? componentNames[componentKey]}
        </Typography>

        {Object.entries(fieldsDef).map(([fieldName, info]) => {
          if (componentData[fieldName] == null) {
            return null; // Skip missing fields
          }

          const value = formatField(componentData[fieldName], info.unit);
          return (
            <Typography key={fieldName} variant="body2" sx={{ mb: 0.5 }}>
              {info.label}: <strong>{value}</strong>
            </Typography>
          );
        })}
      </CardContent>
    </Card>
  );
};


/**
 * TaskDataViewer: A card that displays the entire TaskData similarly
 * to how SimulationSummary displays results:
 *  - "Task Data" header
 *  - Subcomponent cards (one for each portion of TaskData) laid out horizontally
 */
export const TaskDataViewer: React.FC<{ data: TaskData }> = ({ data }) => {

  // small hack to place the Config component last
  const orderedComponentKeys = Object.keys(fieldMappings).sort(
      (key) => key == "config" ? 1 : -1) as (keyof TaskData)[];

  return (
    <Card elevation={3} sx={{ margin: 2 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Components
        </Typography>

        {/*
          Horizontal layout for subcomponent cards,
          scrolling if there are many
        */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'row',
            overflowX: 'auto',
            paddingY: 1,
          }}
        >
          {orderedComponentKeys.flatMap((key) => {
            const componentData = data[key];
            if (!componentData) return [];

            // solar_panels is an array; render each panel separately
            if (Array.isArray(componentData)) {
              return componentData.map((item, idx) => (
                <ComponentDetails
                  key={`${key}-${idx}`}
                  componentKey={key}
                  componentData={item}
                  titleOverride={`${componentNames[key]} ${idx + 1}`} // solar_panels numbering
                />
              ));
            }

            return (
              <ComponentDetails
                key={key}
                componentKey={key}
                componentData={componentData}
              />
            );
          })}
        </Box>
      </CardContent>
    </Card>
  );
};

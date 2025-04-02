import React from "react";

import Icon from "@mdi/react";
import {
  mdiEvStation, mdiGreenhouse, mdiHeatPump,
  mdiHome, mdiHomeBattery, mdiServer, mdiSolarPowerVariant,
  mdiTransmissionTower,
  mdiWaterBoiler, mdiGasBurner
} from "@mdi/js";


import type { ComponentType } from "../../Models/Core/ComponentBuilder"

/**
 * An object mapping each ComponentType to
 * - the human-friendly `displayName`
 * - an `icon` (JSX / ReactNode) for rendering
 */
export const componentInfoLookup: Record<
  ComponentType,
  { icon: React.ReactNode; displayName: string }
> = {
  building: {
    icon: <Icon path={mdiHome} size={2}/>,
    displayName: "Building",
  },
  data_centre: {
    icon: <Icon path={mdiServer} size={2}/>,
    displayName: "Data Centre",
  },
  domestic_hot_water: {
    icon: <Icon path={mdiWaterBoiler} size={2}/>,
    displayName: "Domestic Hot Water",
  },
  electric_vehicles: {
    icon: <Icon path={mdiEvStation} size={2}/>,
    displayName: "Electric Vehicles",
  },
  energy_storage_system: {
    icon: <Icon path={mdiHomeBattery} size={2}/>,
    displayName: "Energy Storage System",
  },
  gas_heater: {
    icon: <Icon path={mdiGasBurner} size={2}/>,
    displayName: "Gas Heater",
  },
  grid: {
    icon: <Icon path={mdiTransmissionTower} size={2}/>,
    displayName: "Grid",
  },
  heat_pump: {
    icon: <Icon path={mdiHeatPump} size={2}/>,
    displayName: "Heat Pump",
  },
  mop: {
    icon: <Icon path={mdiGreenhouse} size={2}/>,
    displayName: "MOP",
  },
  renewables: {
    icon: <Icon path={mdiSolarPowerVariant} size={2}/>,
    displayName: "Renewables",
  },
};

/**
 * get an icon and displayName for a given component
 */
export const getComponentInfo = (type: ComponentType) => {
  return componentInfoLookup[type];
}

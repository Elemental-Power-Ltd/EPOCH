import type {SiteMetrics} from "../State/types.ts"
import {formatCarbon, formatCarbonCost, formatPounds, formatYears, formatEnergy} from "./displayFunctions";

/** All keys that really exist on SiteMetrics */
export type MetricKey = keyof SiteMetrics;

export type iconEnum = 'Carbon' | 'Pound' | 'Gas' | 'Electricity' | 'Year';

/** Immutable definition for one metric */
export interface MetricDefinition {
    /** The key inside `SiteMetrics` */
    key: MetricKey;
    /** Human label shown in the UI */
    label: string;
    /** enum to hint at the desired Icon **/
    icon: iconEnum;
    /** Function that turns the raw number into a displayable string */
    format: (v: number | undefined) => string;
    /** OPTIONAL dynamic colour rule */
    color?: (v: number | undefined) => "action" | "error";
}

const fmtEnergy = (v: number | undefined) => formatEnergy(v, 100);
// when shortfall > 0 we want to display the icon with the 'error' color state
const shortfallColour = (v: number | undefined) =>
    (v ?? 0) > 0 ? "error" : "action";

/** Look‑up table — **one line per metric, ONE place to maintain** */
export const metricDefs: Record<MetricKey, MetricDefinition> = {
    carbon_balance_scope_1: {
        key: "carbon_balance_scope_1",
        label: "Scope 1 Savings",
        icon: 'Carbon',
        format: formatCarbon
    },
    carbon_balance_scope_2: {
        key: "carbon_balance_scope_2",
        label: "Scope 2 Savings",
        icon: 'Carbon',
        format: formatCarbon
    },
    carbon_balance_total: {
        key: "carbon_balance_total",
        label: "Total Carbon Savings",
        icon: 'Carbon',
        format: formatCarbon,
    },
    carbon_cost: {
        key: "carbon_cost",
        label: "Carbon Cost",
        icon: 'Carbon',
        format: formatCarbonCost,
    },
    meter_balance: {
        key: "meter_balance",
        label: "Meter Balance",
        icon: 'Pound',
        format: formatPounds,
    },
    operating_balance: {
        key: "operating_balance",
        label: "Operating Balance",
        icon: 'Pound',
        format: formatPounds,
    },
    cost_balance: {
        key: "cost_balance",
        label: "Cost Balance",
        icon: 'Pound',
        format: formatPounds,
    },
    npv_balance: {
        key: "npv_balance",
        label: "NPV Balance",
        icon: 'Pound',
        format: formatPounds,
    },
    capex: {
        key: "capex",
        label: "CAPEX",
        icon: 'Pound',
        format: formatPounds,
    },
    payback_horizon: {
        key: "payback_horizon",
        label: "Payback Horizon",
        icon: 'Year',
        format: formatYears,
    },
    annualised_cost: {
        key: "annualised_cost",
        label: "Annualised Cost",
        icon: "Pound",
        format: formatPounds,
    },

    total_gas_used: {
        key: "total_gas_used",
        label: "Gas Used",
        icon: "Gas",
        format: fmtEnergy,
    },
    total_electricity_imported: {
        key: "total_electricity_imported",
        label: "Electricity Imported",
        icon: "Electricity",
        format: fmtEnergy,
    },
    total_electricity_generated: {
        key: "total_electricity_generated",
        label: "Electricity Generated",
        icon: "Electricity",
        format: fmtEnergy,
    },
    total_electricity_exported: {
        key: "total_electricity_exported",
        label: "Electricity Exported",
        icon: "Electricity",
        format: fmtEnergy,
    },
    total_electrical_shortfall: {
        key: "total_electrical_shortfall",
        label: "Electrical Shortfall",
        icon: "Electricity",
        format: fmtEnergy,
        color: shortfallColour,
    },
    total_heat_shortfall: {
        key: "total_heat_shortfall",
        label: "Heat Shortfall",
        icon: "Gas",
        format: fmtEnergy,
        color: shortfallColour,
    },
    total_ch_shortfall: {
        key: "total_ch_shortfall",
        label: "CH Shortfall",
        icon: "Gas",
        format: fmtEnergy,
        color: shortfallColour,
    },
    total_dhw_shortfall: {
        key: "total_dhw_shortfall",
        label: "DHW Shortfall",
        icon: "Gas",
        format: fmtEnergy,
        color: shortfallColour,
    },
    total_gas_import_cost: {
        key: "total_gas_import_cost",
        label: "Gas Import Cost",
        icon: "Pound",
        format: formatPounds,
    },
    total_electricity_import_cost: {
        key: "total_electricity_import_cost",
        label: "Electricity Import Cost",
        icon: "Pound",
        format: formatPounds,
    },
    total_electricity_export_gain: {
        key: "total_electricity_export_gain",
        label: "Electricity Export Gain",
        icon: "Pound",
        format: formatPounds,
    },
    total_meter_cost: {
        key: "total_meter_cost",
        label: "Total Meter Cost",
        icon: "Pound",
        format: formatPounds,
    },
    total_operating_cost: {
        key: "total_operating_cost",
        label: "Total Operating Cost",
        icon: "Pound",
        format: formatPounds,
    },
    total_net_present_value: {
        key: "total_net_present_value",
        label: "Net Present Value",
        icon: "Pound",
        format: formatPounds,
    },

    baseline_gas_used: {
        key: "baseline_gas_used",
        label: "Baseline Gas Used",
        icon: "Gas",
        format: fmtEnergy,
    },
    baseline_electricity_imported: {
        key: "baseline_electricity_imported",
        label: "Baseline Electricity Imported",
        icon: "Electricity",
        format: fmtEnergy,
    },
    baseline_electricity_generated: {
        key: "baseline_electricity_generated",
        label: "Baseline Electricity Generated",
        icon: "Electricity",
        format: fmtEnergy,
    },
    baseline_electricity_exported: {
        key: "baseline_electricity_exported",
        label: "Baseline Electricity Exported",
        icon: "Electricity",
        format: fmtEnergy,
    },
    baseline_electrical_shortfall: {
        key: "baseline_electrical_shortfall",
        label: "Baseline Electrical Shortfall",
        icon: "Electricity",
        format: fmtEnergy,
    },
    baseline_heat_shortfall: {
        key: "baseline_heat_shortfall",
        label: "Baseline Heat Shortfall",
        icon: "Gas",
        format: fmtEnergy,
    },
    baseline_ch_shortfall: {
        key: "baseline_ch_shortfall",
        label: "Baseline Cooling Shortfall",
        icon: "Gas",
        format: fmtEnergy,
    },
    baseline_dhw_shortfall: {
        key: "baseline_dhw_shortfall",
        label: "Baseline DHW Shortfall",
        icon: "Gas",
        format: fmtEnergy,
    },
    baseline_gas_import_cost: {
        key: "baseline_gas_import_cost",
        label: "Baseline Gas Import Cost",
        icon: "Pound",
        format: formatPounds,
    },
    baseline_electricity_import_cost: {
        key: "baseline_electricity_import_cost",
        label: "Baseline Elec. Import Cost",
        icon: "Pound",
        format: formatPounds,
    },
    baseline_electricity_export_gain: {
        key: "baseline_electricity_export_gain",
        label: "Baseline Elec. Export Gain",
        icon: "Pound",
        format: formatPounds,
    },
    baseline_meter_cost: {
        key: "baseline_meter_cost",
        label: "Baseline Meter Cost",
        icon: "Pound",
        format: formatPounds,
    },
    baseline_operating_cost: {
        key: "baseline_operating_cost",
        label: "Baseline Operating Cost",
        icon: "Pound",
        format: formatPounds,
    },
    baseline_net_present_value: {
        key: "baseline_net_present_value",
        label: "Baseline NPV",
        icon: "Pound",
        format: formatPounds,
    },
};


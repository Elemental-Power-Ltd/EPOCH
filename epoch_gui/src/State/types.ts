import {Dayjs} from "dayjs";

export interface TaskObjectives {
    capex: boolean;
    carbon_balance_scope_1: boolean;
    carbon_balance_scope_2: boolean;
    carbon_cost: boolean;
    cost_balance: boolean;
    npv_balance: boolean;
    payback_horizon: boolean;
    annualised_cost: boolean;
}

export type OptimisationApproach = "NSGA2" | "GridSearch" | "SeparatedNSGA2" | "Bayesian" | "SeparatedNSGA2xNSGA2";


export interface TaskConfig {
    task_name: string;
    optimiser: OptimisationApproach;
    objectives: TaskObjectives;
    client_id: string;
    start_date: Dayjs | null;
    timestep_minutes: 30 | 60
}

export type SiteRange = any;


export interface OptimisationTaskListEntry {
    task_id: string;
    task_name?: string;
    n_evals: number | null;
    n_saved: number | null;
    exec_time: string | null;
}

export type Grade = 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G';

export interface SiteMetrics {
    meter_balance?: number;
    operating_balance?: number;
    cost_balance?: number;
    npv_balance?: number;

    payback_horizon?: number;

    carbon_balance_scope_1?: number;
    carbon_balance_scope_2?: number;
    carbon_balance_total?: number;
    carbon_cost?: number;

    total_gas_used?: number;
    total_electricity_imported?: number;
    total_electricity_generated?: number;
    total_electricity_exported?: number;
    total_electricity_curtailed?: number;
    total_electricity_used?: number;

    total_electrical_shortfall?: number;
    total_heat_shortfall?: number;
    total_ch_shortfall?: number;
    total_dhw_shortfall?: number;

    capex?: number;
    total_gas_import_cost?: number;
    total_electricity_import_cost?: number;
    total_electricity_export_gain?: number;

    total_meter_cost?: number;
    total_operating_cost?: number;
    annualised_cost?: number;
    total_net_present_value?: number;

    total_scope_1_emissions?: number;
    total_scope_2_emissions?: number;
    total_combined_carbon_emissions?: number;

    scenario_environmental_impact_score?: number;
    scenario_environmental_impact_grade?: Grade;

    baseline_gas_used?: number;
    baseline_electricity_imported?: number;
    baseline_electricity_generated?: number;
    baseline_electricity_exported?: number;
    baseline_electricity_curtailed?: number;
    baseline_electricity_used?: number;

    baseline_electrical_shortfall?: number;
    baseline_heat_shortfall?: number;
    baseline_ch_shortfall?: number;
    baseline_dhw_shortfall?: number;

    baseline_gas_import_cost?: number;
    baseline_electricity_import_cost?: number;
    baseline_electricity_export_gain?: number;

    baseline_meter_cost?: number;
    baseline_operating_cost?: number;
    baseline_net_present_value?: number;

    baseline_scope_1_emissions?: number;
    baseline_scope_2_emissions?: number;
    baseline_combined_carbon_emissions?: number;

    baseline_environmental_impact_score?: number;
    baseline_environmental_impact_grade?: Grade;

}

export interface SiteOptimisationResult {
    site_id: string;
    portfolio_id: string;
    scenario: any;
    metrics: SiteMetrics;
}

export interface PortfolioMetrics {
    meter_balance?: number;
    operating_balance?: number;
    cost_balance?: number;
    npv_balance?: number;

    payback_horizon?: number;

    carbon_balance_scope_1?: number;
    carbon_balance_scope_2?: number;
    carbon_balance_total?: number;
    carbon_cost?: number;

    total_gas_used?: number;
    total_electricity_imported?: number;
    total_electricity_generated?: number;
    total_electricity_exported?: number;
    total_electricity_curtailed?: number;
    total_electricity_used?: number;

    total_electrical_shortfall?: number;
    total_heat_shortfall?: number;
    total_ch_shortfall?: number;
    total_dhw_shortfall?: number;

    capex?: number;
    total_gas_import_cost?: number;
    total_electricity_import_cost?: number;
    total_electricity_export_gain?: number;

    total_meter_cost?: number;
    total_operating_cost?: number;
    annualised_cost?: number;
    total_net_present_value?: number;

    total_scope_1_emissions?: number;
    total_scope_2_emissions?: number;
    total_combined_carbon_emissions?: number;

    baseline_gas_used?: number;
    baseline_electricity_imported?: number;
    baseline_electricity_generated?: number;
    baseline_electricity_exported?: number;
    baseline_electricity_curtailed?: number;
    baseline_electricity_used?: number;

    baseline_electrical_shortfall?: number;
    baseline_heat_shortfall?: number;
    baseline_ch_shortfall?: number;
    baseline_dhw_shortfall?: number;

    baseline_gas_import_cost?: number;
    baseline_electricity_import_cost?: number;
    baseline_electricity_export_gain?: number;

    baseline_meter_cost?: number;
    baseline_operating_cost?: number;
    baseline_net_present_value?: number;

    baseline_scope_1_emissions?: number;
    baseline_scope_2_emissions?: number;
    baseline_combined_carbon_emissions?: number;
}

// fixme - provide a proper type
export interface TaskResult {
    [key: string]: any;
}

export interface PortfolioOptimisationResult {
    task_id: string;
    portfolio_id: string;
    metrics: PortfolioMetrics;
    site_results: SiteOptimisationResult[];
}

export enum HighlightReason {
  BestCostBalance = "best_cost_balance",
  BestCarbonBalance = "best_carbon_balance",
  BestPaybackHorizon = "best_payback_horizon"
}

export interface HighlightedResult {
  portfolio_id: string;
  reason: HighlightReason;
}

export interface OptimisationResultEntry {
    portfolio: PortfolioOptimisationResult[];
    tasks: TaskResult[];
}

export interface Site {
    site_id: string;
    name: string;
}

export interface Client {
    client_id: string;
    name: string;
}

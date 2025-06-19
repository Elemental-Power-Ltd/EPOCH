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

export interface SiteMetrics {
    carbon_balance_scope_1?: number;
    carbon_balance_scope_2?: number;
    carbon_cost?: number;
    cost_balance?: number;
    capex?: number;
    payback_horizon?: number;
    annualised_cost?: number;
    npv_balance?: number;
    total_gas_used?: number;
    total_electricity_imported?: number;
    total_electricity_generated?: number;
    total_electricity_exported?: number;
    total_electrical_shortfall?: number;
    total_heat_shortfall?: number;
    total_gas_import_cost?: number;
    total_electricity_import_cost?: number;
    total_electricity_export_gain?: number;
}

export interface SiteOptimisationResult {
    site_id: string;
    portfolio_id: string;
    scenario: any;
    metrics: SiteMetrics;
}

export interface PortfolioMetrics {
    carbon_balance_scope_1?: number;
    carbon_balance_scope_2?: number;
    carbon_cost?: number;
    cost_balance?: number;
    capex?: number;
    payback_horizon?: number;
    annualised_cost?: number;
    npv_balance?: number;
    total_gas_used?: number;
    total_electricity_imported?: number;
    total_electricity_generated?: number;
    total_electricity_exported?: number;
    total_electrical_shortfall?: number;
    total_heat_shortfall?: number;
    total_gas_import_cost?: number;
    total_electricity_import_cost?: number;
    total_electricity_export_gain?: number;
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

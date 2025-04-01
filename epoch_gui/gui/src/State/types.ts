import {ComponentsMap} from "../Models/Core/ComponentBuilder";
import {SimulationResult} from "../Models/Endpoints";
import {Dayjs} from "dayjs";

export interface TaskObjectives {
    capex: boolean;
    carbon_balance_scope_1: boolean;
    carbon_balance_scope_2: boolean;
    carbon_cost: boolean;
    cost_balance: boolean;
    payback_horizon: boolean;
    annualised_cost: boolean;
}

export type OptimisationApproach = "NSGA2" | "GridSearch";


export interface TaskConfig {
    task_name: string;
    optimiser: OptimisationApproach;
    objectives: TaskObjectives;
    client_id: string;
    start_date: Dayjs | null;
    timestep_minutes: 30 | 60
}

export type SiteRange = any;


export interface OptimiseContainer {
    taskConfig: TaskConfig;
    hyperparameters: {[key in OptimisationApproach]: any };
    portfolioMap: {[key: string]: ComponentsMap}
}


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

export interface PortfolioOptimisationResult {
    task_id: string;
    portfolio_id: string;
    metrics: PortfolioMetrics;
    site_results: SiteOptimisationResult[];
}

export interface OptimisationResultEntry {
    portfolio: PortfolioOptimisationResult[];

    // This should be TaskResult
    tasks: any[];
}


export interface ResultsContainer {
    optimiserServiceStatus: any;
    tasks: OptimisationTaskListEntry[];
}

export interface Site {
    site_id: string;
    name: string;
}

export interface Client {
    client_id: string;
    name: string;
}

export interface AnalysisContainer {
    siteResult: SimulationResult | null;
}


interface GlobalState {
    selectedClient: Client | null;

    availableClients: Client[];
    client_sites: Site[];
}


export interface AppState {
    global: GlobalState
    optimise: OptimiseContainer
    results: ResultsContainer
    analysis: AnalysisContainer


    setOptimiser: (optimiser: OptimisationApproach) => void;
    setHyperparameters: (optimiser: OptimisationApproach, form: any) => void;
    addSiteRange: (site_id: string) => void;
    removeSiteRange: (site_id: string) => void;

    addComponent: (site_id: string, componentKey: string) => void;
    removeComponent: (site_id: string, componentKey: string) => void;
    updateComponent: (site_id: string, componentKey: string, newData: any) => void;
    setComponents: (site_id: string, componentsData: Record<string, any>) => void;
    getComponents: (site_id: string) => any;


    setOptimiserServiceStatus: (status: any) => void;
    setSelectedClient: (client: Client) => void;
    setClientSites: (sites: Site[]) => void;
    setTasks: (tasks: OptimisationTaskListEntry[]) => void;

    setTaskConfig: (config: Partial<TaskConfig>) => void;

    setAvailableClients: (clients: Client[]) => void;

    setAnalysisResult: (siteResult: SimulationResult) => void;
}

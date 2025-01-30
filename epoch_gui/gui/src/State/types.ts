import {ComponentsMap} from "../Models/Core/ComponentBuilder";

export interface TaskObjectives {
    capex: boolean;
    carbon_balance_scope_1: boolean;
    carbon_balance_scope_2: boolean;
    carbon_cost: boolean;
    cost_balance: boolean;
    payback_horizon: boolean;
    annualised_cost: boolean;
}


export interface TaskConfig {
    task_name: string;
    optimiser: "NSGA2" | "GridSearch";
    objectives: TaskObjectives;
    client_id: string;
    start_date: string;
    duration: "year";
    timestep_minutes: 30 | 60
}

export type SiteRange = any;


export interface OptimiseContainer {
    taskConfig: TaskConfig;
    hyperparameters: any;
    portfolioMap: {[key: string]: ComponentsMap}
}


export interface OptimisationTaskListEntry {
    task_id: string;
    task_name?: string;
    result_ids: string[] | null;
    n_evals: number | null;
    exec_time: string | null;
}

export interface SiteOptimisationResult {
    site_id: string;
    portfolio_id: string;
    scenario: any;
    metric_carbon_balance_scope_1?: number;
    metric_carbon_balance_scope_2?: number;
    metric_carbon_cost?: number;
    metric_cost_balance?: number;
    metric_capex?: number;
    metric_payback_horizon?: number;
    metric_annualised_cost?: number;
}


export interface PortfolioOptimisationResult {
    task_id: string;
    portfolio_id: string;
    metric_carbon_balance_scope_1?: number;
    metric_carbon_balance_scope_2?: number;
    metric_carbon_cost?: number;
    metric_cost_balance?: number;
    metric_capex?: number;
    metric_payback_horizon?: number;
    metric_annualised_cost?: number;
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

    currentTask: OptimisationTaskListEntry | null;
    currentTaskResults: PortfolioOptimisationResult[];
    currentPortfolioResult: PortfolioOptimisationResult | null;
}

export interface Site {
    site_id: string;
    name: string;
}

export interface Client {
    client_id: string;
    name: string;
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


    setOptimiser: (optimiser: string) => void;
    setGridConfig: (form: any) => void;
    setGAConfig: (form: any) => void;
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
    setCurrentTask: (task: OptimisationTaskListEntry) => void;
    setCurrentTaskResults: (results: PortfolioOptimisationResult[]) => void;
    setCurrentPortfolioResult: (portfolio_result: PortfolioOptimisationResult) => void;

    setTaskConfig: (config: Partial<TaskConfig>) => void;

    setAvailableClients: (clients: Client[]) => void;
}

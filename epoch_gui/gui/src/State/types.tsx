export interface RunContainer {
    searchParameters: any;
    optimisers: any;
    selectedOptimiser: string
    availableSites: string[];
    selectedSite: string;
}


export interface Task {
    task_id: string;
    site_id: string;
    task_name?: string;
    result_ids: string[];
    n_evals: number;
    exec_time: string;
}

export interface OptimisationResult {
    task_id: string;
    result_id: string;

    solution: { [key: string]: number };

    n_evals?: number;

    exec_time?: string;

    objective_values: {
        carbon_balance: number;
        cost_balance: number;
        capex: number;
        payback_horizon: number;
        annualised_cost: number;
    };

    completed_at: string; // ISO 8601
}


export interface ResultsContainer {
    optimiserServiceStatus: any;
    tasks: Task[];

    currentTask: Task | null;
    currentTaskResults: OptimisationResult[];
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
    client: Client
    client_sites: Site[];
}


export interface AppState {
    global: GlobalState
    run: RunContainer
    results: ResultsContainer


    setSite: (site: string) => void;
    setOptimiser: (optimiser: string) => void;
    setGridConfig: (form: any) => void;
    setGAConfig: (form: any) => void;
    setSearchParameters: (form: any) => void;
    setOptimiserServiceStatus: (status: any) => void;
    setClient: (client: Client) => void;
    setSites: (sites: Site[]) => void;
    setTasks: (tasks: Task[]) => void;
    setCurrentTask: (task: Task) => void;
    setCurrentTaskResults: (results: OptimisationResult[]) => void;
}

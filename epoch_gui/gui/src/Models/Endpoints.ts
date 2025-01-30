

export interface SubmitSimulationRequest {
    task_data: any;

    site_data: any;
}


export type ReportDataType = { [key: string]: number[] };


export interface SimulationResult {
    objectives: any;

    report_data: ReportDataType | null;
}

export type Objective =
  | "carbon_balance_scope_1"
  | "carbon_balance_scope_2"
  | "cost_balance"
  | "capex"
  | "payback_horizon"
  | "annualised_cost"
  | "carbon_cost";


/**
 * The Optimisation definition for an individual site
 */
export interface Site {
    // FIXME - remove once optimisation service no longer expects a name
    name: string;
    site_range: any;
    site_data: any;
}

export interface OptimiserData {
    name: "NSGA2" | "GridSearch";
    hyperparameters: any;
}


export interface SubmitOptimisationRequest {
    name: string;
    optimiser: OptimiserData;
    objectives: Objective[];
    portfolio: Site[];
    portfolio_constraints: any;
    client_id: string;
}

export interface SubmitOptimisationResponse {
    task_id: string;
}
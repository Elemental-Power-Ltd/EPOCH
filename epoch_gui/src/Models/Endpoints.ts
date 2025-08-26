import {HighlightedResult, PortfolioOptimisationResult, SiteMetrics} from "../State/types.ts";

interface SiteMetaData {
    site_id: string;
    start_ts: string;
    end_ts: string;
}


export interface SubmitSimulationRequest {
    task_data: any;

    site_data: SiteMetaData;
}

export interface ReproduceSimulationRequest {
    portfolio_id: string;
    site_id: string;
}


export type ReportDataType = { [key: string]: number[] | null };
export type NonNullReportDataType = { [key: string]: number[]};


interface FabricIntervention {
    cost: number;
    reduced_hload: number[];
}

export interface EpochSiteData {
    start_ts: string;
    end_ts: string;

    baseline: any;

    building_eload: number[];
    building_hload: number[];
    ev_eload: number[];
    dhw_demand: number[];
    air_temperature: number[];
    grid_co2: number[];
    solar_yields: number[][];
    import_tariffs: number[][];
    fabric_interventions: FabricIntervention[];

    ashp_input_table: number[][];
    ashp_output_table: number[][];
}

export interface SimulationResult {
    metrics: SiteMetrics;

    report_data: ReportDataType | null;

    // the TaskData,SiteData pair used to produce this result
    task_data: any;
    site_data: EpochSiteData | null
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
    site_data: SiteMetaData;
}

export interface OptimiserData {
    name: "NSGA2" | "GridSearch" | "SeparatedNSGA2" | "SeparatedNSGA2xNSGA2" | "Bayesian";
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

export interface OptimisationResultsResponse {
    portfolio_results: PortfolioOptimisationResult[];
    highlighted_results: HighlightedResult[];
}


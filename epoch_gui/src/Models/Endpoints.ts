import { TaskData } from "../Components/TaskDataViewer/TaskData.ts";
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


export interface FabricIntervention {
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

export type DayOfInterestType =
    "maxgeneration" |
    "maxbatterythroughput" |
    "maxselfconsumption" |
    "maxheating" |
    "maxdemand" |
    "maxcost" |
    "maxheatshortfall" |
    "maximportshortfall" |
    "maxdhwdemand"


export interface DayOfInterest {
    day_type: DayOfInterestType;
    name: string;
    start_ts: string;
    end_ts: string;
}

export interface SimulationResult {
    metrics: SiteMetrics;

    report_data: ReportDataType | null;

    // the TaskData,SiteData pair used to produce this result
    task_data: any;
    site_data: EpochSiteData | null
    days_of_interest: DayOfInterest[] | null;
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


export type SiteId = string;
export type Component = string;

export type ValuesParam = number[] | string[];
export type FixedParam = number | string;

export interface MinMaxParam<T extends number = number> {
  min: T;
  max: T;
  count: number;
}

export interface Param {
  name: string;
  units: string | null;
  considered: ValuesParam | MinMaxParam | FixedParam;
}

export type GuiParamDict = Record<string, Param>;

export type SearchSpaces = Record<SiteId, Record<Component, GuiParamDict | GuiParamDict[]>>;

export interface SearchInfo {
    total_options_considered: number;
    site_options_considered: Record<SiteId, number>;
}

export interface OptimisationResultsResponse {
    portfolio_results: PortfolioOptimisationResult[];
    highlighted_results: HighlightedResult[];
    hints: Record<string, BundleHint>;
    search_spaces: SearchSpaces;
    search_info: SearchInfo;
}


export interface ListBundlesResponse {
    bundle_id: string;
    name: string;
    is_complete: boolean;
    is_error: boolean;
    site_id: string;
    start_ts: string | null;
    end_ts: string | null;
    created_at: string;
    available_datasets: string[];
}

export type MountType = "building-integrated" | "free"

export interface SolarLocation {
    site_id: string;
    renewables_location_id: string | null;
    name: string | null;
    azimuth: number | null;
    tilt: number | null;
    maxpower: number | null;
    mounting_type: MountType;
}

export interface TariffMetadata {
    dataset_id: string;
    site_id: string;
    created_at: string;
    provider: string;  // enum
    product_name: string;
    tariff_name: string;
    valid_from: string;
    valid_to: string;
    day_cost: number | null;
    night_cost: number | null;
    peak_cost: number | null;
}

export interface HeatingLoadMetadata {
    site_id: string;
    dataset_id: string;
    created_at: string;
    params: any;
    interventions: string[];  // enum
    generation_method: string;  // enum
    peak_hload: number | null;
}

export interface BundleHint {
    site_id: string;
    bundle_id: string;
    renewables: SolarLocation[] | null;
    tariffs: TariffMetadata[] | null;
    baseline: TaskData | null;
    heating: HeatingLoadMetadata[] | null;
}

export interface SiteDataWithHints {
    siteData: EpochSiteData;
    hints: BundleHint | null;
}

export type FuelType = "gas" | "elec"

export interface UploadMeterFileRequest {
    file: File;
    site_id: string;
    fuel_type: FuelType;
    disaggregation_info: null;
}

export interface UploadMeterFileResponse {
    dataset_id: string;
    created_at: string;
    site_id: string;
    fuel_type: FuelType;
    reading_type: "manual" | "automatic" | "halfhourly";
    filename: string | null;
    is_synthesised: boolean;
    start_ts: string;
    end_ts: string;
}

export interface PhppMetadata {
    filename: string | null;
    site_id: string;
    internal_volume: number;
    air_changes: number;
    floor_area: number;
    structure_id: string;
    created_at: string;
}

export interface addSiteRequest {
    client_id: string;
    site_id: string;
    name: string;
    location: string;
    coordinates: [number, number];
    address: string;
    epc_lmk: string | null;
    dec_lmk: string | null;
}

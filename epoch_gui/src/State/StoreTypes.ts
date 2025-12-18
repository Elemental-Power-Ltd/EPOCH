import {Client, OptimisationApproach, OptimisationTaskListEntry, Site, TaskConfig} from "./types.ts";
import {SimulationResult} from "../Models/Endpoints.ts";
import {ComponentsMap} from "../Models/Core/ComponentBuilder.ts";

export interface GlobalState {
    selectedClient: Client | null;

    availableClients: Client[];
    client_sites: Site[];
}

export type GlobalSlice = {
    global: GlobalState;
    setSelectedClient: (client: Client) => void;
    setAvailableClients: (clients: Client[]) => void;
    setClientSites: (sites: Site[]) => void;
    addClientSite: (site: Site) => void;
}

export interface OptimiseState {
    taskConfig: TaskConfig;
    hyperparameters: { [key in OptimisationApproach]: any };
    portfolioMap: { [key: string]: ComponentsMap }
}

export type OptimiserSlice = {
    optimise: OptimiseState;
    setOptimiser: (optimiser: OptimisationApproach) => void;
    setHyperparameters: (optimiser: OptimisationApproach, form: any) => void;
    addSiteRange: (site_id: string, baseline: any) => void;
    removeSiteRange: (site_id: string) => void;
    addComponent: (site_id: string, componentKey: string) => void;
    removeComponent: (site_id: string, componentKey: string) => void;
    updateComponent: (site_id: string, componentKey: string, newData: any) => void;
    setComponents: (site_id: string, componentsData: Record<string, any>) => void;
    getComponents: (site_id: string) => any;
    setTaskConfig: (config: Partial<TaskConfig>) => void;
}

export interface ResultsState {
    optimiserServiceStatus: any;
    tasks: OptimisationTaskListEntry[];
}

export type ResultsSlice = {
    results: ResultsState;
    setOptimiserServiceStatus: (status: any) => void;
    setTasks: (tasks: OptimisationTaskListEntry[]) => void;
}

export interface AnalysisState {
    siteResult: SimulationResult | null;
}

export type AnalysisSlice = {
    analysis: AnalysisState;
    setAnalysisResult: (siteResult: SimulationResult | null) => void;
}

export type AppState =
    & GlobalSlice
    & AnalysisSlice
    & ResultsSlice
    & OptimiserSlice

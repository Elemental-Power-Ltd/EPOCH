import {create} from 'zustand'

import DefaultGrid from "../util/json/default/DefaultGridConfig.json";
import DefaultGA from "../util/json/default/DefaultGAConfig.json";
import DefaultSearchParameters from "../util/json/default/DefaultSearchParameters.json";


interface RunContainer {
    searchParameters: any;
    optimisers: any;
    selectedOptimiser: string
    availableSites: string[];
    selectedSite: string;
}


interface Result {
    taskID: string;
    capex: number;
    carbon_balance: number;
    annualised_cost: number;
    payback_horizon: number;
    cost_balance: number;

    time_taken: number;
}

interface ResultsContainer {
    optimiserServiceStatus: any;
    results: [];
}



interface AppState {
    run: RunContainer
    results: ResultsContainer

    setSite: (site: string) => void;
    setOptimiser: (optimiser: string) => void;

    setGridConfig: (form: any) => void;
    setGAConfig: (form: any) => void;

    setSearchParameters: (form: any) => void;

    setOptimiserServiceStatus: (status: any) => void;
}


export const useEpochStore = create<AppState>()((set) => ({
    run: {
        searchParameters: DefaultSearchParameters,
        optimisers: {
            gridSearch: DefaultGrid,
            geneticAlgorithm: DefaultGA
        },
        selectedOptimiser: "GridSearch",
        availableSites: ["Mount Hotel", "Retford Town Hall", "10 Downing Street", "Sydney Opera House"],
        selectedSite: "Mount Hotel"
    },
    results: {
        optimiserServiceStatus: {},
        results: []
    },

    setSite: (site: string) => set((state) => ({run: {...state.run, selectedSite: site}})),
    setOptimiser: (optimiser: string) => set((state) => ({run: {...state.run, selectedOptimiser: optimiser}})),

    setGridConfig: (form: any) => set((state) => ({run: {...state.run, optimisers: {...state.run.optimisers, gridSearch: form}}})),
    setGAConfig: (form: any) => set((state) => ({run: {...state.run, optimisers: {...state.run.optimisers, geneticAlgorithm: form}}})),

    setSearchParameters: (form: any) => set((state) => ({run: {...state.run, searchParameters: form}})),

    setOptimiserServiceStatus: (status: any) => set((state) => ({results: {...state.results, optimiserServiceStatus: status}}))

}))


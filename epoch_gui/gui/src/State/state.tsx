import {create} from 'zustand'

import DefaultGrid from "../util/json/default/DefaultGridConfig.json";
import DefaultGA from "../util/json/default/DefaultGAConfig.json";
import DefaultSearchParameters from "../util/json/default/DefaultSearchParameters.json";

import {AppState, ResultsContainer, RunContainer, Client, Site, Task, OptimisationResult} from "./types"


const defaultRunContainer: RunContainer = {
    searchParameters: DefaultSearchParameters,
    optimisers: {
        gridSearch: DefaultGrid,
        geneticAlgorithm: DefaultGA
    },
    selectedOptimiser: "GridSearch",
    availableSites: ["Mount Hotel", "Retford Town Hall", "10 Downing Street", "Sydney Opera House"],
    selectedSite: "Mount Hotel"
}

const defaultResultsContainer: ResultsContainer = {
    optimiserServiceStatus: {
        status: 'OFFLINE',
        queue: {},
        service_uptime: 0
    },
    tasks: [],
    currentTask: null,
    currentTaskResults: []
}

export const useEpochStore = create<AppState>()((set) => ({
    global: {
        client: {
            client_id: "demo",
            name: "Jewelery Quarter Businesses",
        },
        client_sites: []
    },
    run: defaultRunContainer,
    results: defaultResultsContainer,

    setSite: (site: string) => set((state) => ({run: {...state.run, selectedSite: site}})),
    setOptimiser: (optimiser: string) => set((state) => ({run: {...state.run, selectedOptimiser: optimiser}})),

    setGridConfig: (form: any) => set((state) => ({run: {...state.run, optimisers: {...state.run.optimisers, gridSearch: form}}})),
    setGAConfig: (form: any) => set((state) => ({run: {...state.run, optimisers: {...state.run.optimisers, geneticAlgorithm: form}}})),

    setSearchParameters: (form: any) => set((state) => ({run: {...state.run, searchParameters: form}})),

    setOptimiserServiceStatus: (status: any) => set((state) => ({results: {...state.results, optimiserServiceStatus: status}})),

    // changing the client should invalidate/reset a lot of the other state and needs careful attention
    // The safest way to do this is to reset all the container states to their default state
    setClient: (client: Client) => set((state) => (
        {
            global: {...state.global, client: client, client_sites: []},
            run: defaultRunContainer,
            results: defaultResultsContainer
        }
    )),
    setSites: (sites: Site[]) => set((state) => ({global: {...state.global, client_sites: sites}})),
    setTasks: (tasks: Task[]) => set((state) => ({results: {...state.results, tasks: tasks}})),

    setCurrentTask: (task: Task) => set((state) => ({results: {...state.results, currentTask: task, currentTaskResults: []}})),
    setCurrentTaskResults: (results: OptimisationResult[]) => set((state) => ({results: {...state.results, currentTaskResults: results}}))

}))

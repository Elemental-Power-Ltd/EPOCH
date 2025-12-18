import {Client, Site} from "./types"
import {defaultOptimiseContainer} from "./OptimiserSlice"
import {defaultResultsContainer} from "./ResultsSlice"
import {defaultAnalysisContainer} from "./AnalysisSlice";
import {StateCreator} from "zustand";
import {AppState, GlobalSlice} from "./StoreTypes.ts";


export const createGlobalSlice: StateCreator<AppState, [], [], GlobalSlice> = (set, _get, _api) => ({
  global: {
    selectedClient: null,
    availableClients: [],
    client_sites: []
  },

  // changing the client should invalidate/reset a lot of the other state and needs careful attention
  // The safest way to do this is to reset all the container states to their default state
  setSelectedClient: (client: Client) =>
    set((state) => ({
      global: { ...state.global, selectedClient: client, client_sites: [] },

      // Reset optimiser slice to default:
      optimise: defaultOptimiseContainer,

      // Reset results slice to default:
      results: defaultResultsContainer,

      // Reset analysis slice to default:
      analysis: defaultAnalysisContainer
    })),

  setAvailableClients: (clients: Client[]) =>
    set((state) => ({
      global: { ...state.global, availableClients: clients }
    })),

  setClientSites: (sites: Site[]) =>
    set((state) => ({
      global: { ...state.global, client_sites: sites }
    })),

  addClientSite: (site: Site) =>
    set((state) => ({
      global: {...state.global, client_sites: [...state.global.client_sites, site]},
    })),
})

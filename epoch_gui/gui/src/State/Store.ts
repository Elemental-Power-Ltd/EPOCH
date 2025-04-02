import { create } from 'zustand'
import { AppState } from "./StoreTypes.ts"
import { createGlobalSlice } from "./GlobalSlice"
import { createOptimiserSlice } from "./OptimiserSlice"
import { createResultsSlice } from "./ResultsSlice"
import { createAnalysisSlice } from "./AnalysisSlice"

export const useEpochStore = create<AppState>()((set, get, api) => ({
  ...createGlobalSlice(set, get, api),
  ...createOptimiserSlice(set, get, api),
  ...createResultsSlice(set, get, api),
  ...createAnalysisSlice(set, get, api),
}))

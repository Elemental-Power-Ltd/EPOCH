import { create } from 'zustand'
import { AppState } from "./types"
import { createGlobalSlice } from "./GlobalSlice"
import { createOptimiserSlice } from "./OptimiserSlice"
import { createResultsSlice } from "./ResultsSlice"

export const useEpochStore = create<AppState>()((...a) => ({
  ...createGlobalSlice(...a),
  ...createOptimiserSlice(...a),
  ...createResultsSlice(...a),
}))

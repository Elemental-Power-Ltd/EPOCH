import {SimulationResult} from "../Models/Endpoints";
import {StateCreator} from "zustand";
import {AnalysisState, AnalysisSlice, AppState} from "./StoreTypes.ts";


export const defaultAnalysisContainer: AnalysisState = {
    siteResult: null
}

export const createAnalysisSlice: StateCreator<AppState, [], [], AnalysisSlice>
    = (set, _get, _api) => ({

    analysis: defaultAnalysisContainer,

    setAnalysisResult: (siteResult: SimulationResult | null) =>
        set((state) => ({
            analysis: {
                ...state.analysis,
                siteResult: siteResult
            }
        }))
})
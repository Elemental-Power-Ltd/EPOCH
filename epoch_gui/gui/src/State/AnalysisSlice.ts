import {AnalysisContainer} from "./types";
import {SimulationResult} from "../Models/Endpoints";


export const defaultAnalysisContainer: AnalysisContainer = {
    siteResult: null
}

export const createAnalysisSlice = (set, get, api) => ({
    analysis: defaultAnalysisContainer,

    setAnalysisResult: (siteResult: SimulationResult | null) =>
        set((state) => ({
            analysis: {
                ...state.analysis,
                siteResult: siteResult
            }
        }))
})
import {StateCreator} from "zustand"
import {OptimisationTaskListEntry} from "./types"
import {AppState, ResultsState, ResultsSlice} from "./StoreTypes.ts";
import {OptimiserStatus} from "../endpoints.tsx";


export const defaultResultsContainer: ResultsState = {
  optimiserServiceStatus: 'OFFLINE',
  tasks: [],
}

export const createResultsSlice: StateCreator<AppState, [], [], ResultsSlice> =
    (set, _get, _api) => ({

    results: defaultResultsContainer,

  setOptimiserServiceStatus: (status: OptimiserStatus) =>
    set((state) => ({
      results: {
        ...state.results,
        optimiserServiceStatus: status
      }
    })),

  setTasks: (tasks: OptimisationTaskListEntry[]) =>
    set((state) => ({
      results: {
        ...state.results,
        tasks: tasks
      }
    })),
})

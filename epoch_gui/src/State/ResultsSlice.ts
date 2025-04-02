import {StateCreator} from "zustand"
import {OptimisationTaskListEntry} from "./types"
import {AppState, ResultsState, ResultsSlice} from "./StoreTypes.ts";


export const defaultResultsContainer: ResultsState = {
  optimiserServiceStatus: {
    status: 'OFFLINE',
    queue: {},
    service_uptime: 0
  },
  tasks: [],
}

export const createResultsSlice: StateCreator<AppState, [], [], ResultsSlice> =
    (set, _get, _api) => ({

    results: defaultResultsContainer,

  setOptimiserServiceStatus: (status: any) =>
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

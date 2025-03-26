import {
    ResultsContainer,
    OptimisationTaskListEntry,
} from "./types"

export const defaultResultsContainer: ResultsContainer = {
  optimiserServiceStatus: {
    status: 'OFFLINE',
    queue: {},
    service_uptime: 0
  },
  tasks: [],
}

export const createResultsSlice = (set, get, api) => ({
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

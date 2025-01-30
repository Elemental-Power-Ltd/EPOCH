import {
    ResultsContainer,
    OptimisationTaskListEntry,
    PortfolioOptimisationResult
} from "./types"

export const defaultResultsContainer: ResultsContainer = {
  optimiserServiceStatus: {
    status: 'OFFLINE',
    queue: {},
    service_uptime: 0
  },
  tasks: [],
  currentTask: null,
  currentTaskResults: [],
  currentPortfolioResult: null,
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

  setCurrentTask: (task: OptimisationTaskListEntry) =>
    set((state) => ({
      results: {
        ...state.results,
        currentTask: task,
        currentTaskResults: [],
        currentPortfolioResult: null
      }
    })),

  setCurrentTaskResults: (results: PortfolioOptimisationResult[]) =>
    set((state) => ({
      results: {
        ...state.results,
        currentTaskResults: results
      }
    })),

    setCurrentPortfolioResult: (portfolio_result: PortfolioOptimisationResult) => {
      set((state) => ({
          results: {
              ...state.results,
              currentPortfolioResult: portfolio_result
          }
      }))
    }
})

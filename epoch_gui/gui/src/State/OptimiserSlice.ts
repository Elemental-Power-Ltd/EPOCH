import DefaultGrid from "../util/json/default/DefaultGridConfig.json"
import DefaultGA from "../util/json/default/DefaultGAConfig.json"
import { getInitialComponentsMap, hardcodedConfig } from "../Components/ComponentBuilder/initialState"
import {
  TaskConfig,
  OptimiseContainer
} from "./types"

const defaultTaskConfig: TaskConfig = {
  task_name: "",
  optimiser: "NSGA2",
  objectives: {
    capex: false,
    carbon_balance_scope_1: false,
    carbon_balance_scope_2: false,
    carbon_cost: false,
    cost_balance: false,
    payback_horizon: false,
    annualised_cost: false
  },
  client_id: "",
  start_date: "2022-01-01 00:00:00+00:00",
  duration: "year",
  timestep_minutes: 30
}

export const defaultOptimiseContainer: OptimiseContainer = {
  taskConfig: defaultTaskConfig,
  hyperparameters: {
    gridSearch: DefaultGrid,
    geneticAlgorithm: DefaultGA
  },
  portfolioMap: {}
}

export const createOptimiserSlice = (set, get, api) => ({
  optimise: defaultOptimiseContainer,

  setOptimiser: (optimiser: string) =>
    set((state) => ({ optimise: { ...state.optimise, selectedOptimiser: optimiser } })),

  setGridConfig: (form: any) =>
    set((state) => ({
      optimise: {
        ...state.optimise,
        hyperparameters: {
          ...state.optimise.hyperparameters,
          gridSearch: form
        }
      }
    })),

  setGAConfig: (form: any) =>
    set((state) => ({
      optimise: {
        ...state.optimise,
        hyperparameters: {
          ...state.optimise.hyperparameters,
          geneticAlgorithm: form
        }
      }
    })),

  // add a new ComponentBuilderState to the portfolio for a given site_id
  addSiteRange: (site_id: string) =>
    set((state) => ({
      optimise: {
        ...state.optimise,
        portfolioMap: {
          ...state.optimise.portfolioMap,
          [site_id]: getInitialComponentsMap("SiteRangeMode")
        }
      }
    })),

  removeSiteRange: (site_id: string) =>
    set((state) => {
      const { [site_id]: _, ...rest } = state.optimise.portfolioMap
      return {
        optimise: {
          ...state.optimise,
          portfolioMap: rest
        }
      }
    }),

  addComponent: (site_id: string, componentKey: string) =>
    set((state) => {
      const siteMap = state.optimise.portfolioMap[site_id]
      if (!siteMap) return {}

      return {
        optimise: {
          ...state.optimise,
          portfolioMap: {
            ...state.optimise.portfolioMap,
            [site_id]: {
              ...siteMap,
              [componentKey]: {
                ...siteMap[componentKey],
                selected: true
              }
            }
          }
        }
      }
    }),

  removeComponent: (site_id: string, componentKey: string) =>
    set((state) => {
      const siteMap = state.optimise.portfolioMap[site_id]
      if (!siteMap) return {}

      return {
        optimise: {
          ...state.optimise,
          portfolioMap: {
            ...state.optimise.portfolioMap,
            [site_id]: {
              ...siteMap,
              [componentKey]: {
                ...siteMap[componentKey],
                selected: false
              }
            }
          }
        }
      }
    }),

  updateComponent: (site_id: string, componentKey: string, newData: any) =>
    set((state) => {
      const siteMap = state.optimise.portfolioMap[site_id]
      if (!siteMap) return {}

      return {
        optimise: {
          ...state.optimise,
          portfolioMap: {
            ...state.optimise.portfolioMap,
            [site_id]: {
              ...siteMap,
              [componentKey]: {
                ...siteMap[componentKey],
                data: newData
              }
            }
          }
        }
      }
    }),

  setComponents: (site_id: string, componentsData: Record<string, any>) =>
    set((state) => {
      const siteMap = state.optimise.portfolioMap[site_id]
      if (!siteMap) return {}

      const newSiteMap = { ...siteMap }

      Object.keys(newSiteMap).forEach((componentKey) => {
        if (componentKey in componentsData) {
          // if the component is present:
          //   - update the data field
          //   - set selected to true
          newSiteMap[componentKey] = {
            ...newSiteMap[componentKey],
            selected: true,
            data: componentsData[componentKey]
          }
        } else {
          // The component is not present
          //  mark as not 'selected' and leave the data field as is
          newSiteMap[componentKey] = {
            ...newSiteMap[componentKey],
            selected: false
          }
        }
      })

      return {
        optimise: {
          ...state.optimise,
          portfolioMap: {
            ...state.optimise.portfolioMap,
            [site_id]: newSiteMap
          }
        }
      }
    }),

  getComponents: (site_id: string): any => {
    const siteMap = get().optimise.portfolioMap[site_id]
    if (!siteMap) return {}

    const data: Record<string, any> = {}

    // Add the data for each 'selected' component
    for (const componentKey in siteMap) {
      if (siteMap[componentKey].selected) {
        data[componentKey] = siteMap[componentKey].data
      }
    }

    // FIXME - this needs looking at
    // Add the config
    data["config"] = hardcodedConfig

    return data
  },

  setTaskConfig: (config: Partial<TaskConfig>) =>
    set((state) => ({
      optimise: {
        ...state.optimise,
        taskConfig: {
          ...state.optimise.taskConfig,
          ...config
        }
      }
    })),
})

import {StateCreator} from "zustand"
import dayjs from "dayjs";

import {OptimisationApproach, TaskConfig} from "./types"
import {AppState, OptimiseState, OptimiserSlice} from "./StoreTypes.ts";

import DefaultGrid from "../util/json/default/DefaultGridConfig.json"
import DefaultNSGA2 from "../util/json/default/DefaultNSGA2Config.json"
import DefaultSeparatedNSGA2 from "../util/json/default/DefaultSeparatedNSGA2Config.json"
import DefaultBayesian from "../util/json/default/DefaultBayesianConfig.json"
import DefaultSeparatedNSGA2xNSGA2 from "../util/json/default/DefaultSeparatedNSGA2xNSGA2Config.json"
import DefaultConfig from "../util/json/default/DefaultTaskConfig.json"
import {getInitialComponentsMap} from "../Components/ComponentBuilder/initialState"
import {ComponentType} from "../Models/Core/ComponentBuilder.ts";

const defaultTaskConfig: TaskConfig = {
  task_name: "",
  optimiser: "NSGA2",
  objectives: {
    capex: false,
    carbon_balance_scope_1: false,
    carbon_balance_scope_2: false,
    carbon_balance_total: false,
    carbon_cost: false,
    npv_balance: false,
    cost_balance: false,
    payback_horizon: false,
    return_on_investment: false,
    annualised_cost: false
  },
  client_id: "",
  start_date: dayjs("2022-01-01 00:00:00+00:00"),
  timestep_minutes: 30
}

export const defaultOptimiseContainer: OptimiseState = {
  taskConfig: defaultTaskConfig,
  hyperparameters: {
    GridSearch: DefaultGrid,
    SeparatedNSGA2: DefaultSeparatedNSGA2,
    Bayesian: DefaultBayesian,
    NSGA2: DefaultNSGA2,
    SeparatedNSGA2xNSGA2: DefaultSeparatedNSGA2xNSGA2
  },
  portfolioMap: {}
}

export const createOptimiserSlice: StateCreator<AppState, [], [], OptimiserSlice>
    = (set, get, _api) => ({

  optimise: defaultOptimiseContainer,

  setOptimiser: (optimiser: OptimisationApproach) =>
      set((state) => ({
        optimise:
            {
              ...state.optimise, taskConfig: {
                ...state.optimise.taskConfig,
                optimiser: optimiser
              }
            }
      })),

  setHyperparameters: (optimiser: OptimisationApproach, form: any) =>
      set((state) => ({
        optimise : {
          ...state.optimise,
          hyperparameters: {
            ...state.optimise.hyperparameters,
            [optimiser]: form
          }
        }
    })),

  // add a new ComponentBuilderState to the portfolio for a given site_id
  addSiteRange: (site_id: string, baseline: any) =>
    set((state) => ({
      optimise: {
        ...state.optimise,
        portfolioMap: {
          ...state.optimise.portfolioMap,
          [site_id]: {
            config: DefaultConfig,
            components: getInitialComponentsMap("SiteRangeMode", baseline)
          }
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
      const siteInfo = state.optimise.portfolioMap[site_id]
      if (!siteInfo) return {}

      return {
        optimise: {
          ...state.optimise,
          portfolioMap: {
            ...state.optimise.portfolioMap,
            [site_id]: {
              ...siteInfo,
              components: {
                ...siteInfo.components,
                [componentKey]: {
                  ...siteInfo.components[componentKey as ComponentType],
                  selected: true
                }
              }
            }
          }
        }
      }
    }),

  removeComponent: (site_id: string, componentKey: string) =>
    set((state) => {
      const siteInfo = state.optimise.portfolioMap[site_id]
      if (!siteInfo) return {}

      return {
        optimise: {
          ...state.optimise,
          portfolioMap: {
            ...state.optimise.portfolioMap,
            [site_id]: {
              ...siteInfo,
              components: {
                ...siteInfo.components,
                [componentKey]: {
                  ...siteInfo.components[componentKey as ComponentType],
                  selected: false
                }
              }
            }
          }
        }
      }
    }),

  updateComponent: (site_id: string, componentKey: string, newData: any) =>
    set((state) => {
      const siteInfo = state.optimise.portfolioMap[site_id]
      if (!siteInfo) return {}

      return {
        optimise: {
          ...state.optimise,
          portfolioMap: {
            ...state.optimise.portfolioMap,
            [site_id]: {
              ...siteInfo,
              components: {
                ...siteInfo.components,
                [componentKey]: {
                  ...siteInfo.components[componentKey as ComponentType],
                  data: newData
                }
              }
            }
          }
        }
      }
    }),

  setComponents: (site_id: string, componentsData: Record<string, any>) =>
    set((state) => {
      const siteInfo = state.optimise.portfolioMap[site_id]
      if (!siteInfo) return {}

      const newSiteInfo = { ...siteInfo }

      Object.keys(newSiteInfo.components).forEach((componentKey) => {
        if (componentKey in componentsData) {
          // if the component is present:
          //   - update the data field
          //   - set selected to true
          newSiteInfo.components[componentKey as ComponentType] = {
            ...newSiteInfo.components[componentKey as ComponentType],
            selected: true,
            data: componentsData[componentKey]
          }
        } else {
          // The component is not present
          //  mark as not 'selected' and leave the data field as is
          newSiteInfo.components[componentKey as ComponentType] = {
            ...newSiteInfo.components[componentKey as ComponentType],
            selected: false
          }
        }
      })

      return {
        optimise: {
          ...state.optimise,
          portfolioMap: {
            ...state.optimise.portfolioMap,
            [site_id]: newSiteInfo
          }
        }
      }
    }),

  getComponents: (site_id: string): any => {
    const siteInfo = get().optimise.portfolioMap[site_id];
    if (!siteInfo) return {}
    const siteMap = siteInfo.components;

    const data: Record<string, any> = {}

    // Add the data for each 'selected' component
    for (const componentKey in siteMap) {
      if (siteMap[componentKey as ComponentType].selected) {
        data[componentKey] = siteMap[componentKey as ComponentType].data
      }
    }

    return data
  },
  setConfig: (site_id: string, config: any) => set((state) => (
      {
        optimise: {
          ...state.optimise,
          portfolioMap: {
            ...state.optimise.portfolioMap,
            [site_id]: {
              ...state.optimise.portfolioMap[site_id],
              config: config
            }
          }
        }
      }
  )),

  setOptimiserConfig: (config: Partial<TaskConfig>) =>
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

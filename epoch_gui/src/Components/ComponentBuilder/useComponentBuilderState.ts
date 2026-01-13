import { useState } from "react";
import {BuilderMode, ComponentType, ComponentsMap, SiteInfo} from "../../Models/Core/ComponentBuilder";
import { getInitialComponentsMap } from "./initialState";
import TaskDataSchema from "../../util/json/schema/TaskDataSchema.json";
import SiteRangeSchema from "../../util/json/schema/HumanFriendlySiteRangeSchema.json";
import DefaultConfig from "../../util/json/default/DefaultTaskConfig.json"

export interface ComponentBuilderState {
  siteInfo: SiteInfo;
  addComponent: (component: ComponentType) => void;
  removeComponent: (component: ComponentType) => void;
  updateComponent: (component: ComponentType, data: any) => void;
  setComponents: (data: any) => void;
  getComponents: () => any;
  setConfig: (config: any) => void;
  schema: any;
}

/**
 * This hook provides the logic necessary to modify which components are selected in either a TaskData or SiteRange.
 *
 * Default values for each component are set upon initialisation.
 * Add/Removing components simply specifies whether that component should be included or not.
 */
export const useComponentBuilderState = (mode: BuilderMode, baseline: any): ComponentBuilderState => {
  const initialSiteInfo: SiteInfo = {
    components: getInitialComponentsMap(mode, baseline),
    config: DefaultConfig,
  }
  const schema = (mode === "TaskDataMode") ? TaskDataSchema : SiteRangeSchema;

  const [siteInfo, setSiteInfo] = useState<SiteInfo>(initialSiteInfo);

  /**
   * Mark the named component as present.
   * @param component the name/key of the component
   */
  const addComponent = (component: ComponentType) => {
    setSiteInfo((prev) => ({
      ...prev,
      components: {
        ...prev.components,
        [component]: {...prev.components[component], selected: true},
      }
    }));
  };

    /**
   * Mark the named component as not present.
   * @param component the name/key of the component
   */
  const removeComponent = (component: ComponentType) => {
    setSiteInfo(prev => ({
      ...prev,
      components: {
        ...prev.components,
        [component]: {...prev.components[component], selected: false},
      }
    }));
  };

  /**
   * Change the 'data' for a single component
   * @param component the name/key of the component
   * @param newData the new data values
   */
  const updateComponent = (component: ComponentType, newData: any) => {
    setSiteInfo(prev => ({
      ...prev,
      components: {
        ...prev.components,
        [component]: {...prev.components[component], data: newData},
      }
    }));
  };

  /**
   * Update the data fields of each component with an externally provided TaskData/SiteRange
   * @param components
   */
  const setComponents = (components: any) => {
    setSiteInfo(prev => {
      const newComponentsMap = { ...prev.components };

      for (const stringKey in prev.components) {
        const componentKey = stringKey as ComponentType;

        if (componentKey in components) {
          // set this component as 'selected' and apply the data from taskData
          newComponentsMap[componentKey] = {
            ...newComponentsMap[componentKey],
            selected: true,
            data: components[componentKey]
          };

        } else {
          // set this component as not 'selected' (leaving the previous value for the data)
          newComponentsMap[componentKey] = {
            ...newComponentsMap[componentKey],
            selected: false,
          };
        }
      }
      return {components: newComponentsMap, config: prev.config};
    });
  };

  /**
   * Extract the TaskData out of the components state
   */
  const getComponents = (): ComponentsMap => {
    const data: Record<string, any> = {};

    // Add the data for each 'selected' component
    for (const stringKey in siteInfo.components) {
      const componentKey = stringKey as ComponentType;

      if (siteInfo.components[componentKey].selected) {
        data[componentKey] = siteInfo.components[componentKey].data;
      }
    }

    return data as ComponentsMap;

  };

  const setConfig = (config: any) => {
    setSiteInfo((prev) => (
        {
          ...prev,
          config: config
        }
    ))
  }

  return {
    siteInfo,
    addComponent,
    removeComponent,
    updateComponent,
    setComponents,
    getComponents,
    setConfig,
    schema
  };
};

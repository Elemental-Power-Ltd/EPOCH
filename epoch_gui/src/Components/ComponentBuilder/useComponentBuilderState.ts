import { useState } from "react";
import { BuilderMode, ComponentType, ComponentsMap } from "../../Models/Core/ComponentBuilder";
import { getInitialComponentsMap } from "./initialState";
import TaskDataSchema from "../../util/json/schema/TaskDataSchema.json";
import SiteRangeSchema from "../../util/json/schema/HumanFriendlySiteRangeSchema.json";


export interface ComponentBuilderState {
  componentsState: any;
  addComponent: (component: ComponentType) => void;
  removeComponent: (component: ComponentType) => void;
  updateComponent: (component: ComponentType, data: any) => void;
  setComponents: (data: any) => void;
  getComponents: () => any;
  schema: any;
}

/**
 * This hook provides the logic necessary to modify which components are selected in either a TaskData or SiteRange.
 *
 * Default values for each component are set upon initialisation.
 * Add/Removing components simply specifies whether that component should be included or not.
 */
export const useComponentBuilderState = (mode: BuilderMode, baseline: any): ComponentBuilderState => {
  const initialState = getInitialComponentsMap(mode, baseline);
  const schema = (mode === "TaskDataMode") ? TaskDataSchema : SiteRangeSchema;

  const [componentsState, setComponentsState] = useState<ComponentsMap>(initialState);

  /**
   * Mark the named component as present.
   * @param component the name/key of the component
   */
  const addComponent = (component: ComponentType) => {
    setComponentsState((prev) => ({
      ...prev,
      [component]: {...prev[component], selected: true},
    }));
  };

    /**
   * Mark the named component as not present.
   * @param component the name/key of the component
   */
  const removeComponent = (component: ComponentType) => {
    setComponentsState(prev => ({
      ...prev,
      [component]: {...prev[component], selected: false},
    }));
  };

  /**
   * Change the 'data' for a single component
   * @param component the name/key of the component
   * @param newData the new data values
   */
  const updateComponent = (component: ComponentType, newData: any) => {
    setComponentsState(prev => ({
      ...prev,
      [component]: { ...prev[component], data: newData },
    }));
  };

  /**
   * Update the data fields of each component with an externally provided TaskData/SiteRange
   * @param components
   */
  const setComponents = (components: any) => {
    setComponentsState(prev => {
      const newComponentsMap = { ...prev };

      for (const stringKey in prev) {
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
      return newComponentsMap;
    });
  };

  /**
   * Extract the TaskData out of the components state
   */
  const getComponents = () => {
    const data: Record<string, any> = {};

    // Add the data for each 'selected' component
    for (const stringKey in componentsState) {
      const componentKey = stringKey as ComponentType;

      if (componentsState[componentKey].selected) {
        data[componentKey] = componentsState[componentKey].data;
      }
    }

    return data;

  };

  return {
    componentsState,
    addComponent,
    removeComponent,
    updateComponent,
    setComponents,
    getComponents,
    schema
  };
};

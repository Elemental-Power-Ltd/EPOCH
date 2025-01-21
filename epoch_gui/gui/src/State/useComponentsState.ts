import { useState } from "react";
import { ComponentType, ComponentsMap } from "../Models/Core/TaskData";
import { initialComponents, hardcodedConfig} from "./initialState";

/**
 * This hook provides the logic necessary to modify which components are selected in TaskData
 * Default values for each component are set upon initialisation.
 * Add/Removing components simples specifies whether that component should be included or not.
 */
export const useTaskComponentsState = () => {

  const [componentsState, setComponentsState] = useState<ComponentsMap>(initialComponents);

  /**
   * Add a component to the TaskData.
   * @param component the name/key of the component
   */
  const addComponent = (component: ComponentType) => {
    setComponentsState((prev) => ({
      ...prev,
      [component]: {...prev[component], selected: true},
    }));
  };

    /**
   * Remove a component from the TaskData.
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
   * Update the data fields of each component with an externally provided TaskData
   * @param taskData
   */
  const setTaskData = (taskData: any) => {
    // FIXME: this currently ignores the config because we are hardcoding at 10m
    setComponentsState(prev => {
      const newComponentsMap = { ...prev };

      for (const componentKey in prev) {
        if (componentKey in taskData) {
          // set this component as 'selected' and apply the data from taskData
          newComponentsMap[componentKey] = {
            ...newComponentsMap[componentKey],
            selected: true,
            data: taskData[componentKey]
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
  const getTaskData = () => {
    const taskData = {};

    // Add the data for each 'selected' component
    for (const componentKey in componentsState) {
      if (componentsState[componentKey].selected) {
        taskData[componentKey] = componentsState[componentKey].data;
      }
    }

    // Add the config
    taskData["config"] = hardcodedConfig;

    return taskData;

  };

  return {
    componentsState,
    addComponent,
    removeComponent,
    updateComponent,
    setTaskData,
    getTaskData,
  };
};

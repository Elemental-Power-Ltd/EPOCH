import validator from "@rjsf/validator-ajv8";
import TaskDataSchema from "../../util/json/schema/TaskDataSchema.json";
import {RJSFSchema} from "@rjsf/utils";


export interface ValidationResult {
  valid: boolean;
  result: any;
}

export const validateTaskData = (taskData: any) => {
        const result = validator.validateFormData(taskData, TaskDataSchema as RJSFSchema);

        return {
            valid: result.errors.length === 0,
            result: result,
        };
    };

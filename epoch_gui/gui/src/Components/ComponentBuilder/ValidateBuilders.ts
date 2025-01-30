import validator from "@rjsf/validator-ajv8";
import TaskDataSchema from "../../util/json/schema/TaskDataSchema.json";
import SiteRangeSchema from "../../util/json/schema/HumanFriendlySiteRangeSchema.json"
import {RJSFSchema} from "@rjsf/utils";


export interface ValidationResult {
  valid: boolean;
  result: any;
}

export const validateTaskData = (taskData: any): ValidationResult => {
        const result = validator.validateFormData(taskData, TaskDataSchema as RJSFSchema);

        return {
            valid: result.errors.length === 0,
            result: result,
        };
    };

export const validateSiteRange = (siteRange: any): ValidationResult => {
    const result = validator.validateFormData(siteRange, SiteRangeSchema as RJSFSchema);

    // TODO
    //  SiteRange validation should be slightly more sophisticated
    //  If we succesfully validate against the 'HumanFriendly' site range,
    //  we should also convert with ExpandSiteRange and validate against the second schema
    //  (or alternatively, consider allowing the backend to perform that expansion)

    return {
        valid: result.errors.length === 0,
        result: result,
    };
}

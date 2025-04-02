import validator from "@rjsf/validator-ajv8";
import TaskDataSchema from "../../util/json/schema/TaskDataSchema.json";
import SiteRangeSchema from "../../util/json/schema/HumanFriendlySiteRangeSchema.json"
import {RJSFSchema, RJSFValidationError} from "@rjsf/utils";


export interface ValidationResult {
  valid: boolean;
  result: any;

  // any errors within a result parsed into strings for semi-human-readable display
  stringErrors: string[];
}

export const validateTaskData = (taskData: any): ValidationResult => {
        const result = validator.validateFormData(taskData, TaskDataSchema as RJSFSchema);

        return {
            valid: result.errors.length === 0,
            result: result,
            stringErrors: errorsToStrings(result.errors)
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
        stringErrors: errorsToStrings(result.errors)
    };
}

/**
 * convert errors to strings
 * @param errors a list of errors as (semi) human-readable strings
 */
const errorsToStrings = (errors: RJSFValidationError[]): string[] => {
    return errors.map(error => (
        `${error.property} ${error.message}`
    ));
}

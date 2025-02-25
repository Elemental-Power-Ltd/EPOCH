import {validateSiteRange} from "./ValidateBuilders";

export interface PortfolioValidationResult {
  success: boolean;
  data?: Record<string, any>;
}

interface ExpandSiteRangeSuccess {
  success: true;
  data: Record<string, any>;
}

interface ExpandSiteRangeFailure {
  success: false;
  errors: string[];
}


/**
 * Transform a 'human-friendly' siteRange containing {min,max,step} values
 * into one containing only arrays of values instead.
 *
 * This function is needed to provide feedback to the user, so we do not immediately return upon an error.
 * Parsing will continue to discover all errors and return them to the user.
 * @param siteRange
 * @return a boolean indicating success and either a list of errors or the expanded site range
 */
const expandSiteRange = (siteRange: any): ExpandSiteRangeSuccess | ExpandSiteRangeFailure => {
  const expandedSiteRange: Record<string, any> = {};
  const errors: string[] = [];

  // We run validation in two parts here:
  //  1. validation against the JSON schema definition for a HumanFriendlySiteRange
  //  2. manual validation uncovered through trying to expand {min,max,step} into an array

  // Perform the automated schema validation first
  const rjsfResult = validateSiteRange(siteRange);

  if (!rjsfResult.valid) {
    errors.push(...rjsfResult.stringErrors);
  }

  // manual validation
  for (const component of Object.keys(siteRange)) {
    // try and expand the component
    const expandResult = expandComponent(component, siteRange[component]);

    // store the errors or the result as appropriate
    if (!expandResult.success) {
      errors.push(...expandResult.errors)
    } else {
      expandedSiteRange[component] = expandResult.data;
    }
  }

  // failure if we encountered any errors
  if (errors.length > 0) {
    return {success: false, errors: errors}
  }
  return {success: true, data: expandedSiteRange};
};

interface ExpandComponentSuccess {
  success: true
  data: Record<string, any>
}

interface ExpandComponentFailure {
  success: false
  errors: string[];
}

/**
 * Try and expand the individual Components within a SiteRange
 * @param componentName the name of this component - used to provide a descriptive error
 * @param component the component data
 */
const expandComponent = (componentName: string, component: Record<string,any>): ExpandComponentSuccess | ExpandComponentFailure => {
  const expandedComponent: Record<string, any> = {};
  const componentErrors: string[] = [];

  for (const prop of Object.keys(component)) {
    const propName = `${componentName}.${prop}`
    const {expanded, errors} = expandInternals(component[prop], propName);
    expandedComponent[prop] = expanded;
    componentErrors.push(...errors);
  }

  if (componentErrors.length) {
    return {success: false, errors: componentErrors};
  }
  return {success: true, data: expandedComponent};
};

/**
 * A recursive method to expand out any Objects or Arrays within a Component
 * @param value a property within a component
 * @param propName the name of the property - to provide a descriptive error
 */
const expandInternals = (value: any, propName: string): {expanded: any; errors: string[] } => {
  const errors: string[] = [];

  if(Array.isArray(value)) {
    // This is an array, try and expand each element within it, propagating errors
    const expandedArray: any[] = [];
    for (let i = 0; i < value.length; i++) {
      const {expanded: expandedChild, errors: childErrors} = expandInternals(value[i], `${propName}[${i}]`);
      expandedArray.push(expandedChild);
      errors.push(...childErrors);
    }
    return {expanded: expandedArray, errors: errors};
  } else if (value !== null && typeof value === "object") {
    // This is an Object
    const isMinMaxStep = "min" in value && "max" in value && "step" in value;

    if (isMinMaxStep) {
      const expandedMinMaxStep = expandMinMaxStep(value, propName);
      if ("error" in expandedMinMaxStep) {
        errors.push(expandedMinMaxStep.error);
        return {expanded: null, errors: errors};
      } else {
        return {expanded: expandedMinMaxStep.expanded, errors: errors};
      }
    } else {
      const expandedObject: Record<string, any> = {};
      for (const key of Object.keys(value)) {
        const {expanded, errors: childErrors} = expandInternals(value[key], `${propName}.${key}`)
        expandedObject[key] = expanded;
        errors.push(...childErrors);
      }
      return {expanded: expandedObject, errors: errors};
    }

  } else {
    // This is a primitive and not an array or object
    // just return the value as is (and no errors)
    return {expanded: value, errors: []}
  }
}

interface ExpandStepSuccess {
  expanded: number[];
}

interface ExpandStepFailure {
  error: string;
}

interface MinMaxStep {
  min: number;
  max: number;
  step: number;
}

/**
 * Transform a min/max/step object into the full array of values in that range.
 * (Starting from min and ending at max)
 *
 * If the min/max/step is misconfigured we return an error string instead.
 *
 * This function is written to never exceed max. If the steps do not evenly fit in the range
 * then the final value will be less than max
 * @param value an object with min/max/step properties
 * @param propName the name of the property - to provide a descriptive error
 */
const expandMinMaxStep = (value: MinMaxStep, propName: string): ExpandStepSuccess | ExpandStepFailure => {
  const {min, max, step} = value;

  if (typeof min !== "number" || typeof max !== "number" || typeof step !== "number") {
    return {error: `${propName}: min,max and step must all be numbers.`}
  }

  if (min > max) {
    return {error: `${propName}: Invalid range: min (${min}) > max (${max}).`};
  }
  if (step < 0) {
    return {error: `${propName}: Invalid step: step (${step}) must be >= 0.`};
  }
  if (step === 0 && min !== max) {
    return {error: `${propName}: Invalid combination, min/max differ with 0 step.`};
  }
  if (min === max && step !== 0) {
    return {error: `${propName}: Invalid combination, min/max are equal but step is not 0.`}
  }

  // If min === max, return a single value in the array
  if (min === max) {
    return {expanded: [min]};
  }

  const expandedArray: number[] = [];
  for (let current = min; current <= max; current += step) {
    expandedArray.push(current);
  }
  return {expanded: expandedArray};
}

export default expandSiteRange;

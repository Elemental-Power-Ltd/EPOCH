/**
 * transform a 'human-friendly' siteRange containing {min,max,step}
 * into one containing only arrays of values
 * @param siteRange
 */
const expandSiteRange = (siteRange: any): any => {

  const expandedSiteRange: Record<string, any> = {};

  for (const component of Object.keys(siteRange)) {
    expandedSiteRange[component] = expandComponent(siteRange[component]);
  }

  return expandedSiteRange;
};

const expandComponent = (component: any): any => {
  const expandedComponent: Record<string, any> = {};

  for (const prop of Object.keys(component)) {
    const value = component[prop];

    // Check if this property is a {min,max,step} object
    if (value && typeof value === "object" && "min" in value && "max" in value && "step" in value) {
      const { min, max, step } = value;

      // Throw exceptions if malformed
      if (min > max) {
        throw new Error(`Invalid range: min (${min}) > max (${max}).`);
      }
      if (step < 0) {
        throw new Error(`Invalid step: step (${step}) must be >= 0.`);
      }

      // If min === max, return a single value in the array
      if (min === max) {
        expandedComponent[prop] = [min];
      } else {
        const expandedArray: number[] = [];
        for (let current = min; current <= max; current += step) {
          expandedArray.push(current);
        }
        expandedComponent[prop] = expandedArray;
      }
    } else {
      // if it's not {min,max,step} leave unchanged
      expandedComponent[prop] = value;
    }
  }

  return expandedComponent;
};

export default expandSiteRange;

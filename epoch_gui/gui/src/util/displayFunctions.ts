
// Display prices to the nearest £100
export const formatPounds = (value: number): string => {
    const roundedValue = Math.round(value / 100) * 100;
    return `£${roundedValue.toLocaleString()}`;
};


// Display carbon emissions to the nearest 10kg CO2e
export const formatCarbon = (value: number): string => {
    const roundedValue = Math.round(value / 10) * 10;
    return `${roundedValue.toLocaleString()} kg CO2e`;
};

// Display years to 2 decimal places
export const formatYears = (value: number): string => {
    return `${value.toFixed(2)} years`;
};
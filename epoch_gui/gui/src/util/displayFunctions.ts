
// we don't want to display anything greater than a trillion
// (likely float max or similar)
const one_trillion = 1000000000000

// Display prices to the nearest £100
export const formatPounds = (value: number | undefined): string => {
    if (!Number.isFinite(value) || value === undefined || value > one_trillion ) {
        return "-"
    }

    const roundedValue = Math.round(value / 100) * 100;
    return `£${roundedValue.toLocaleString()}`;
};


// Display carbon emissions to the nearest 10kg CO2e
export const formatCarbon = (value: number | undefined): string => {
    if (!Number.isFinite(value) || value === undefined || value > one_trillion ) {
        return "-"
    }

    const roundedValue = Math.round(value / 10) * 10;
    return `${roundedValue.toLocaleString()} kg CO2e`;
};

export const formatCarbonCost = (value: number | undefined): string => {
    if (!Number.isFinite(value) || value === undefined || value > one_trillion ) {
        return "-"
    }


    const roundedValue = Math.round(value / 10) * 10;
    return `${roundedValue.toLocaleString()} £/tonne`;
};


// Display years to 2 decimal places
export const formatYears = (value: number | undefined): string => {
    if (!Number.isFinite(value) || value === undefined || value > one_trillion ) {
        return "-"
    }

    return `${value.toFixed(2)} years`;
};

// display energy to the nearest 100 kWh
export const formatEnergy = (value: number | undefined): string => {
    if (!Number.isFinite(value) || value === undefined || value > one_trillion ) {
        return "-"
    }
    const roundedValue = Math.round(value / 100) * 100;
    return `${roundedValue.toLocaleString()} kWh`;
}


export const parseISODuration = (duration: string | null): string => {
    if (duration === null) return "-";

    const match = duration.match(/P(?:T)?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(\.\d+)?)S)?/);
    if (!match) return 'Invalid duration';

    // Parse hours, minutes, and seconds (default to 0 if not present)
    const hours = parseFloat(match[1] || '0');
    const minutes = parseFloat(match[2] || '0');
    const seconds = parseFloat(match[3] || '0');

    // Convert to total seconds
    const totalSeconds = hours * 3600 + minutes * 60 + seconds;

    // Calculate days, hours, minutes, and seconds for the final output
    const days = Math.floor(totalSeconds / (3600 * 24));
    let remainingSeconds = totalSeconds % (3600 * 24);
    const displayHours = Math.floor(remainingSeconds / 3600);
    remainingSeconds %= 3600;
    const displayMinutes = Math.floor(remainingSeconds / 60);
    const displaySeconds = remainingSeconds % 60;

    let humanReadableDuration = '';
    if (days > 0) humanReadableDuration += `${days} day${days > 1 ? 's' : ''}, `;
    if (displayHours > 0) humanReadableDuration += `${displayHours} hour${displayHours > 1 ? 's' : ''}, `;
    if (displayMinutes > 0) humanReadableDuration += `${displayMinutes} minute${displayMinutes > 1 ? 's' : ''}, `;
    humanReadableDuration += `${displaySeconds.toFixed(0)} second${displaySeconds !== 1 ? 's' : ''}`;

    return humanReadableDuration;
};

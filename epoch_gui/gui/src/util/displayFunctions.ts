
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


export const parseISODuration = (duration: string): string => {
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

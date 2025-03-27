import {BatteryMode, GasType, HeatSource} from "../Components/TaskDataViewer/TaskData.ts";

// we don't want to display anything greater than a trillion
// (likely float max or similar)
const one_trillion = 1000000000000


// Human-readable labels for enum values
const batteryModeLabels: Record<BatteryMode, string> = {
  [BatteryMode.CONSUME]:      'Consume',
  [BatteryMode.CONSUME_PLUS]: 'Consume Plus',
};

const gasTypeLabels: Record<GasType, string> = {
  [GasType.NATURAL_GAS]:           'Natural Gas',
  [GasType.LIQUID_PETROLEUM_GAS]:  'LPG',
};

const heatSourceLabels: Record<HeatSource, string> = {
  [HeatSource.AMBIENT_AIR]: 'Ambient Air',
  [HeatSource.HOTROOM]:     'Hotroom',
};


export const formatField = (value: unknown, unit?: string): string => {
  const defaultDecimals = 2;

  const unitToFormatter: Record<string, (val: number) => string> = {
    '£': formatPounds,
    'kg CO2e': formatCarbon,
    'kWh': formatEnergy,
    'kW': formatPower,
    '°C': formatTemperature,
    'litres': (val) => `${val.toLocaleString()} L`,
    'decimal %': (val) => `${(val * 100).toFixed(2)}%`
  };

  // If the value is an array (e.g. yield_scalars), keep the original array logic
  if (Array.isArray(value)) {
    return value
        .map((item) => (typeof item === 'number' ? item.toFixed(defaultDecimals) : String(item)))
        .join(', ');
  }

  // If the value is numeric, try to apply a known unit-specific formatter (if `unit` is passed)
  if (typeof value === 'number') {
    if (unit && unitToFormatter[unit]) {
      return unitToFormatter[unit](value);
    }
    // try to treat unitless numbers as integers or failing that decimals
    return Number.isInteger(value) ? (~~value).toString() : value.toFixed(defaultDecimals);
  }

  // If the value is a string, it could be an enum (batteryMode/gasType/heatSource)
  if (typeof value === 'string') {
    if (value in batteryModeLabels) {
      return batteryModeLabels[value as BatteryMode];
    }
    if (value in gasTypeLabels) {
      return gasTypeLabels[value as GasType];
    }
    if (value in heatSourceLabels) {
      return heatSourceLabels[value as HeatSource];
    }
    return value; // normal string
  }

  // Fallback for anything else
  return String(value ?? '');
}



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
    if (!Number.isFinite(value) || value === undefined || value > one_trillion || value < 0 ) {
        return "-"
    }

    return `${value.toFixed(2)} years`;
};

// display energy to the nearest 100 kWh
export const formatEnergy = (value: number | undefined, toNearest?: number): string => {
    if (!Number.isFinite(value) || value === undefined || value > one_trillion ) {
        return "-"
    }
    if (toNearest) {
        value = Math.round(value / toNearest) * toNearest;
    }
    return `${value.toLocaleString()} kWh`;
}

export const formatPower = (value: number | undefined): string => {
    if (!Number.isFinite(value) || value === undefined || value > one_trillion ) {
        return "-"
    }
    return `${value.toLocaleString()} kW`;
}

export const formatTemperature = (value: number | undefined): string => {
    if (!Number.isFinite(value) || value === undefined || value > one_trillion ) {
        return "-"
    }
    return `${value.toLocaleString()} °C`;
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

import { NonNullReportDataType } from "../../Models/Endpoints";

export const removeEmptyVectors = (data: NonNullReportDataType): NonNullReportDataType => {
    return Object.fromEntries(
        Object.entries(data).filter(([_, vector]) => vector.length > 0)
    );
}

const getHue = (color: string): number => {
    // Convert hex to RGB
    const [r, g, b] = color.match(/\w\w/g)!.map((c) => parseInt(c, 16) / 255);

    // Convert RGB to HSL and return the hue (H)
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let hue = 0;
    if (max === min) hue = 0; // No color (grayscale)
    else if (max === r) hue = (60 * ((g - b) / (max - min)) + 360) % 360;
    else if (max === g) hue = (60 * ((b - r) / (max - min)) + 120) % 360;
    else if (max === b) hue = (60 * ((r - g) / (max - min)) + 240) % 360;

    return hue; // Hue in degrees (0–360)
};

export const ensureContrastHue = (color1: string, color2: string, isDarkMode: boolean): string => {
    const hue1 = getHue(color1);
    const hue2 = getHue(color2);

    // Calculate absolute hue difference
    const hueDifference = Math.abs(hue1 - hue2);
    const threshold = 30; // Adjust threshold for sensitivity (degrees)

    if (hueDifference < threshold || hueDifference > 360 - threshold) {
        // If hues are too close, adjust the first color
        return isDarkMode ? '#FFFFFF' : '#000000'; // Default fallback color is white/black for dark/light mode
    }
    return color1;
};

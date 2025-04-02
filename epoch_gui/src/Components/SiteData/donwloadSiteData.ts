import dayjs from "dayjs";

import {EpochSiteData} from "../../Models/Endpoints";


export const downloadJSON = (siteData: EpochSiteData) => {
    const jsonData = JSON.stringify(siteData, null, 2);
    const blob = new Blob([jsonData], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'siteData.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}


export const downloadCSV = (siteData: EpochSiteData) => {
    // Parse start and end times
    const startTime = dayjs(siteData.start_ts);
    const endTime = dayjs(siteData.end_ts);

    // all entries have the same length
    const length = siteData.building_eload.length;

    // interpolate times from startTime to endTime (inclusive).
    // i=0 => startTime, i=length-1 => endTime
    const totalSeconds = endTime.diff(startTime, "second");
    const secondsPerTimestep = length === 0 ? 0 : totalSeconds / length;

    // Build the header row
    const headers: string[] = [
        "time",
        "building_eload",
        "building_hload",
        "ev_eload",
        "dhw_demand",
        "air_temperature",
        "grid_co2",
        // annotate the list of lists with their index
        ...siteData.solar_yields.map((_, i) => `solar_yields[${i}]`),
        ...siteData.import_tariffs.map((_, i) => `import_tariffs[${i}]`),
        ...siteData.fabric_interventions.map((_, i) => `fabric_interventions[${i}]`),
    ];

    // Collect CSV lines in an array
    const csvRows: string[] = [];
    csvRows.push(headers.join(",")); // First line is the header

    // Build each data row
    for (let i = 0; i < length; i++) {
        // The interpolation logic for the times may suffer from rounding errors
        // but we don't care as the CSV is supposed to be indicative only

        const elapsedSeconds = i * secondsPerTimestep;
        const currentTime = startTime.add(elapsedSeconds, "second");
        const roundedTime = currentTime.set("millisecond", 0);
        const rowTime = dayjs(roundedTime).toISOString();

        // Start building the row cells
        const rowCells: (string | number)[] = [];

        // time column
        rowCells.push(rowTime);

        // Single-dimension arrays
        rowCells.push(
            siteData.building_eload[i],
            siteData.building_hload[i],
            siteData.ev_eload[i],
            siteData.dhw_demand[i],
            siteData.air_temperature[i],
            siteData.grid_co2[i]
        );

        // list of lists
        siteData.solar_yields.forEach(solar => {
            rowCells.push(solar[i]);
        });
        siteData.import_tariffs.forEach(tariff => {
            rowCells.push(tariff[i]);
        });

        siteData.fabric_interventions.forEach(intervention => {
            rowCells.push(intervention.reduced_hload[i]);
        });

        // Combine cells into one comma-separated row
        csvRows.push(rowCells.join(","));
    }

    // Convert to a single CSV string
    const csvContent = csvRows.join("\n");

    const blob = new Blob([csvContent], {type: "text/csv;charset=utf-8;"});
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "siteData.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};


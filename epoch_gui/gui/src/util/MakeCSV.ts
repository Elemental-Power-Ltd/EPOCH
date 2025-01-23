import {ReportDataType} from "../Models/Endpoints";

/**
 * Convert a ReportDataType object into CSV format.
 * The first row is the list of keys (headers),
 * followed by rows of numerical data (columns).
 */
function convertReportDataToCSV(reportData: ReportDataType): string {
  const keys = Object.keys(reportData);
  if (!keys.length) {
    return ""; // No data, return an empty CSV
  }

  // Find the maximum length among all arrays
  const maxLength = Math.max(...keys.map((key) => reportData[key].length));

  // Build the header row (comma-separated keys)
  const csvRows = [keys.join(",")];

  // For each row index from 0 up to maxLength - 1
  for (let i = 0; i < maxLength; i++) {
    // Gather each key's value at position i (or blank if none)
    const rowValues = keys.map((key) => {
      const value = reportData[key][i];
      return value !== undefined ? value.toString() : "";
    });
    csvRows.push(rowValues.join(","));
  }

  return csvRows.join("\n");
}

/**
 * onClick function that triggers the CSV download
 * with the filename "reportData.csv".
 */
export function onClickDownloadReportData(reportData: ReportDataType) {
  const csv = convertReportDataToCSV(reportData);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", "reportData.csv");
  link.click();

  // Clean up the URL object
  URL.revokeObjectURL(url);
}

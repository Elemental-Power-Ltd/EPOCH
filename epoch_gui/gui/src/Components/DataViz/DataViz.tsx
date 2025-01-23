import React, {useEffect, useState} from "react";
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import {AdapterDayjs} from "@mui/x-date-pickers/AdapterDayjs";
import dayjs, {Dayjs} from 'dayjs';
import {Select, MenuItem, FormControl, InputLabel, Button} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';

import Plot from 'react-plotly.js';

import {ReportDataType, SimulationResult} from "../../Models/Endpoints";
import {onClickDownloadReportData} from "../../util/MakeCSV";
import {color_map, default_positive_stackbars, default_negative_stackbars, daysOptions} from "./GraphConfig";

interface DataVizProps {
    result: SimulationResult
}

const DataVizContainer: React.FC<DataVizProps> = ({result}) => {

    const reportData = removeEmptyVectors(result.report_data!);

    // Set const values for the assumed first date and sampling frequency in rawData
    const initialDatetime = dayjs("2022-01-01T00:00:00Z"); // Example default initial datetime
    const dataPeriodInMinutes = 30;
    const samplingFrequencySeconds = 1 / (dataPeriodInMinutes * 60); // Example: 1 sample per half hour
    const samplingFrequencyMs = samplingFrequencySeconds / 1000;

    // Initial states - variables for filtering data
    const [selectedStartDatetime, setSelectedStartDatetime] = useState<Dayjs|null>(initialDatetime);
    const [daysToKeep, setDaysToKeep] = useState(1);
    const [rangedData, setRangedData] = useState<ReportDataType>(reportData);

    // Initial states - variable for reacting to browser window size
    const [windowWidth, setWindowWidth] = useState(window.innerWidth);

    // Filter data by number of observations, whenever input from dropdowns changes
    useEffect(() => {
        if (selectedStartDatetime === null) {
            return;
        }

        const initialTimestampMs = initialDatetime.valueOf();
        const startTimestampMs = selectedStartDatetime.valueOf();
        const endTimestampMs = startTimestampMs + daysToKeep * 24 * 60 * 60 * 1000 -1;

        const startIndex = Math.floor((startTimestampMs - initialTimestampMs) * samplingFrequencyMs);
        const endIndex = Math.floor((endTimestampMs - initialTimestampMs) * samplingFrequencyMs);

        // Filter rawData directly by index range
        const filtered: ReportDataType = Object.fromEntries(
            Object.entries(reportData).map(([key, values]) => [key, values.slice(startIndex, endIndex + 1)])
        );

        setRangedData(filtered);
    }, [selectedStartDatetime, daysToKeep]);


    // Remove any entries that aren't in default lists; change sign of negative data
    const filteredAndRangedData = Object.fromEntries(
        Object.entries(rangedData)
            .filter(([key]) => default_positive_stackbars.includes(key) || default_negative_stackbars.includes(key))
            .map(([key, array]) =>
                default_negative_stackbars.includes(key) // condition on whether variable is a negative bar (an energy source)
                    ? [key, array.map(value => -value)]  // transform if so
                    : [key, array]) // otherwise, leave as-is
    );


    // We add an offset to the X values so that the bars are centred on the midpoint of each timerange
    // ie centred around 00:15 rather than 00:00 for the first entry in the day
    const offset_to_centre = dataPeriodInMinutes / 2
    const x_hh = Array.from({ length: daysToKeep * 48 }, (_, i) =>
        dayjs(selectedStartDatetime).add(i*30 + offset_to_centre, 'minute').toDate()
    )
    

    const totals_pos = filteredAndRangedData[Object.keys(filteredAndRangedData)[0]].map((_, i) =>
        Object.entries(filteredAndRangedData)
            .filter(([key]) => default_positive_stackbars.includes(key))
            .reduce((sum, [_, arr]) => sum + arr[i], 0)
    );
    const totals_neg = filteredAndRangedData[Object.keys(filteredAndRangedData)[0]].map((_, i) =>
        Object.entries(filteredAndRangedData)
            .filter(([key]) => default_negative_stackbars.includes(key))
            .reduce((sum, [_, arr]) => sum + arr[i], 0)
    );

    const mycustomdata = Object.keys(filteredAndRangedData).map((key, i) =>
        default_negative_stackbars.includes(key) ? totals_neg[i] : totals_pos[i]
      );

    const stackedChartData_neg = Object.keys(filteredAndRangedData)
        .filter((key) => default_negative_stackbars.includes(key))
        .map((key) => {
            return{
                x: x_hh, //columnLabels,
                y: default_negative_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                name: key,
                type: 'bar',
                marker: {color: color_map[key]},
                customdata: totals_neg,
                hoverinfo: 'name+x+y',
                hovertemplate: 'Value: %{y:.4f}<br>Total draw: %{customdata:.4f}',
        };
        }
    );

    const stackedChartData_pos = Object.keys(filteredAndRangedData)
        .filter((key) => default_positive_stackbars.includes(key))
        .map((key) => {
            return{
            x: x_hh, //columnLabels,
            y: default_positive_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
            name: key,
            type: 'bar',
            marker: {color: color_map[key]},
            customdata: totals_pos,
            hoverinfo: 'x+y+name',
            hovertemplate: 'Value: %{y:.4f}<br>Total supply: %{customdata:.4f}',
        };
        }
    );

    const stackedChartLayout = {
        title: `Half-hourly energy balances across the site`,
        barmode: 'relative',
        xaxis: {title: "Date & Time",
            type: 'date',
            tickformat: "%H:%M",
            dtick: "3600000", // one tick every hour
            range: [new Date(x_hh[0]).getTime() - 1800000 ,
                new Date(x_hh[x_hh.length-1]).getTime() + 1800000 ],
            // tickvals: x_hh,
            tickmode: "array",
            // ticklabelmode: 'period', // Aligns ticks correctly for time ranges
            showgrid: true,
            showticklabels: true,
            tickformatstops: [
              {
                dtickrange: [null, 86400000], // Below one day
                value: '%H:%M\n%d %b', // Format as HH:MM
              },
              {
                dtickrange: [86400000, null], // One day or above
                value: '%H:%M\n%d %b', // Add date and time (day-month on new lines)
              },
            ],
        },
        yaxis: {title: "Energy draw / supply (kWh)"},
        autosize: true, // Disable autosize to control manually
        width: windowWidth * 0.95, // 95% of the window width
        height: windowWidth * 0.95 * 0.4 // Adjust height as needed
        // responsive: true
    }


    // Define dropdown options for line charts
    const variableOptions = Object.keys(rangedData).map((key) => ({value: key, label: key}));
    // Use reactive variables to control the data being shown in the line charts
    // Define states for each panel's two selected variables
    const [panelSelections, setPanelSelections] = useState(
        [{ var1: 'DHW_load', var2: 'DHW_charging' },
        { var1: 'DHW_SoC', var2: 'DHW_charging' },
        { var1: 'PVacGen', var2: 'Grid_Import' },
        { var1: 'Hotel_load', var2: 'ESS_discharge' }]
    );

    // Define a function for handling dropdown variable selection for line charts
    const handleSelectChange = (panelIndex, selectedVar, isVar1) => {
        setPanelSelections((prev) =>
        prev.map((panel, idx) =>
            idx === panelIndex
            ? { ...panel, [isVar1 ? 'var1' : 'var2']: selectedVar }
            : panel
        )
        );
    };

    // Update window width on resize
    useEffect(() => {
        const handleResize = () => setWindowWidth(Math.min(window.innerWidth,1800));
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);
    }, []);


    // Introduce functionality for checking colour contrasts
    const getHue = (color) => {
        // Convert hex to RGB
        const [r, g, b] = color.match(/\w\w/g).map((c) => parseInt(c, 16) / 255);

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

    const ensureContrastHue = (color1, color2) => {
        const hue1 = getHue(color1);
        const hue2 = getHue(color2);

        // Calculate absolute hue difference
        const hueDifference = Math.abs(hue1 - hue2);
        const threshold = 30; // Adjust threshold for sensitivity (degrees)

        if (hueDifference < threshold || hueDifference > 360 - threshold) {
            // If hues are too close, adjust the first color
            return '#000000'; // Default fallback color (e.g., black)
        }
        return color1;
    };

    return (
        <div style={{//border: '2px dotted rgb(96 139 168)',
            display: 'flex', flexDirection: 'column',
            margin: '1em 0 0 0', width: '100%', alignItems: 'center', justifySelf: 'center',
            boxSizing: 'border-box'}}
        >
            <div id="range-picker-group" style={{//border: '2px dotted rgb(96 139 168)',
                display: 'flex', justifyContent: 'center', gap: '40px'}}
            >
                <div id="datepicker" style={{display: 'flex', alignItems: 'center', gap: '10px'}}
                >
                    {/* Date Picker for Start Date */}
                    <LocalizationProvider dateAdapter={AdapterDayjs}>
                        <DateTimePicker
                            label="Start Date & Time:"
                            value={selectedStartDatetime}
                            onChange={(date) => setSelectedStartDatetime(date)}
                        />
                    </LocalizationProvider>
                </div>

                <div id="dropdown" style={{display: 'flex', alignItems: 'center', gap: '10px'}}
                >
                    <FormControl>
                        <InputLabel id="days-label">Days</InputLabel>
                        <Select
                            labelId="days-label"
                            value={daysToKeep}
                            label="Number of Days"
                            onChange={(e) => setDaysToKeep(e.target.value as number)}
                        >
                            {daysOptions.map((option) => (
                                <MenuItem key={option.value} value={option.value}>
                                    {option.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </div>
                <Button
                    variant="outlined"
                    onClick={() => onClickDownloadReportData(reportData)}
                    startIcon={<DownloadIcon/>}
                    style={{marginRight: '10px'}}
                >
                    Download CSV
                </Button>

            </div>

            {/* Stacked Bar Chart Panel */}
            <div id="stacked-bar-chart" style={{//border: '2px dotted rgb(96 139 168)',
                display: 'flex', width: 0.95*windowWidth, boxSizing: 'border-box' }}
            >
                {/* Render the stacked bar chart */}
                <Plot
                    data={[...stackedChartData_neg, ...stackedChartData_pos]}
                    layout={stackedChartLayout}
                />
            </div>

            {/* Line Chart Panels */}
            <div id="panel-charts" style={{//border: '2px dotted rgb(96 139 168)',
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '20px',
                    marginTop: '20px',
                    width: 0.95*windowWidth, // width of grid
                    boxSizing: 'border-box',
            }}>
                {panelSelections.map((panel, index) => (
                    <div key={index} style={{border: '3px solid rgb(7, 96, 64)',
                        borderRadius: '10px',
                        padding: '1.5%'
                    }}>
                        {/* Dropdowns for Variable Selection */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                            <FormControl sx={{minWidth: 120}}>
                                <InputLabel id={`var1-label-${index}`}>Variable 1</InputLabel>
                                <Select
                                    labelId={`var1-label-${index}`}
                                    id={`var1-select-${index}`}
                                    label="Variable 1"
                                    value={panel.var1}
                                    onChange={(e) => handleSelectChange(index, e.target.value, true)}
                                >
                                    {variableOptions.map((option) => (
                                        <MenuItem key={option.value} value={option.value}>
                                            {option.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <FormControl sx={{minWidth: 120}}>
                                <InputLabel id={`var2-label-${index}`}>Variable 2</InputLabel>
                                <Select
                                    labelId={`var2-label-${index}`}
                                    id={`var2-select-${index}`}
                                    label="Variable 2"
                                    value={panel.var2}
                                    onChange={(e) => handleSelectChange(index, e.target.value, false)}
                                >
                                    {variableOptions.map((option) => (
                                        <MenuItem key={option.value} value={option.value}>
                                            {option.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </div>

                        {/* Plot Line Chart */}
                        <Plot
                        data={[
                            {
                            x: x_hh, // Shared x-axis: filtered date range
                            y: rangedData[panel.var1],
                            name: panel.var1,
                            type: 'scatter',
                            mode: 'lines',
                            line: {
                                color: (() => {
                                    const color1 = color_map[panel.var1] || '#1f77b4';
                                    const color2 = color_map[panel.var2] || '#d96b09';
                                    const result = ensureContrastHue(color1, color2);
                                    return result;
                                  })()
                            },  // Default to blue if not in map
                            },
                            {
                            x: x_hh,
                            y: rangedData[panel.var2],
                            name: panel.var2,
                            type: 'scatter',
                            mode: 'lines',
                            line: {color: color_map[panel.var2] || '#d96b09'}, // Default to dark orange if not in map
                            },
                        ]}
                        layout={{
                            title: {
                                text: (() => {
                                    const color1 = color_map[panel.var1] || '#1f77b4';
                                    const color2 = color_map[panel.var2] || '#d96b09';
                                    const result = ensureContrastHue(color1, color2);
                                    const resulting_text = `<span style="color:${result};">${panel.var1}</span> vs <span style="color:${color2};">${panel.var2}</span>`
                                    return resulting_text;
                                  })()
                            },
                            xaxis: { title: 'Date & Time' },
                            yaxis: { title: 'Value' },
                            margin: { l: 65, r: 65, t: 50, b: 50 },
                            autosize: false, // Disable autosize
                            width: windowWidth * 0.45, // 45% of the window width per panel
                            height: windowWidth * 0.45 * 0.6, // Adjust height as needed
                            showlegend: false
                            //legend:  {
                            //     'x': 0.99,          // x position (0-1 inside plot, >1 outside)
                            //     'y': 1.0,          // y position (0-1)
                            //     'xanchor': 'right', // 'left', 'center', or 'right'
                            //     'yanchor': 'bottom',  // 'top', 'middle', or 'bottom'
                            //     'orientation': 'v'  // 'v' for vertical, 'h' for horizontal
                            // }
                        }}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}

export default DataVizContainer

const removeEmptyVectors = (data: ReportDataType): ReportDataType => {
  return Object.fromEntries(
    Object.entries(data).filter(([_, vector]) => vector.length > 0)
  );
}
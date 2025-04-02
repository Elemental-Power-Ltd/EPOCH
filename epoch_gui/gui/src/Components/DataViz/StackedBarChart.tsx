import React, {useState} from "react";
// @ts-ignore
import Plot from "react-plotly.js"
import {FormControl, InputLabel, Select, MenuItem, useMediaQuery} from "@mui/material"

import {
    color_map,
    elec_supply_stackbars,
    elec_draw_stackbars,
    heat_supply_stackbars,
    heat_draw_stackbars,
    elec_shortfall_stackbars,
    heat_shortfall_stackbars,
    elec_surplus_stackbars,
    heat_surplus_stackbars,
    all_energy_stackbars,
    all_negative_stackbars,
    all_positive_stackbars,
    all_flagged_stackbars,
    stackbarGroups,
    StackbarOption,
} from "./GraphConfig";
import {getAppTheme} from "../../Colours";
import {DataAnnotationMap} from "./TimeSeriesAnnotations";

interface StackedBarChartProps {
    rangedData: DataAnnotationMap;
    xValues: Date[];
    windowWidth: number;
}

export const StackedBarChart: React.FC<StackedBarChartProps> = ({
    rangedData, xValues, windowWidth
}) => {

    const [selectedStackbarGroups, setSelectedStackbarGroups] = useState<StackbarOption>('all');

    // Remove any entries that aren't in default lists; change sign of negative data
    const filteredAndRangedData = Object.fromEntries(
        Object.entries(rangedData)
            .filter(([key]) => all_energy_stackbars.includes(key))
            .map(([key, value]) =>
                all_negative_stackbars.includes(key) // condition on whether variable is a negative bar (an energy source)
                    ? [key, value.data.map(value => -value)]  // transform if so
                    : [key, value.data]) // otherwise, leave as-is
    );

    // Calculate the negative total (energy draw)
    const negativeTotals = filteredAndRangedData[Object.keys(filteredAndRangedData)[0]].map((_, i) =>
        Object.entries(filteredAndRangedData)
            .filter(([key]) => all_negative_stackbars.includes(key))
            .reduce((sum, [_, arr]) => sum + arr[i], 0)
    );

    // Calculate the positive total (energy supply)
    const positiveTotals = filteredAndRangedData[Object.keys(filteredAndRangedData)[0]].map((_, i) =>
        Object.entries(filteredAndRangedData)
            .filter(([key]) => all_positive_stackbars.includes(key))
            .reduce((sum, [_, arr]) => sum + arr[i], 0)
    );

    const getMarker = (key: string) => {
        if (all_flagged_stackbars.includes(key)) {
            // shortfall and surplus amounts are indicated in hatched markings so that they stand out
            return {
                pattern: {
                    fgcolor: color_map[key as keyof typeof color_map],
                    bgcolor: '#000000',
                    shape: "/", size: 10, solidity: 0.7
                }
            }
        }
        // otherwise return a solid colour defined in the color_map
        return {color: color_map[key as keyof typeof color_map]}
    }


    const elecDrawChartData = Object.keys(filteredAndRangedData)
        .filter((key) => elec_draw_stackbars.includes(key))
        .map((key) => {
                return {
                    x: xValues, //columnLabels,
                    y: elec_draw_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                    name: rangedData[key]?.name || key,
                    type: 'bar',
                    marker: getMarker(key),
                    customdata: negativeTotals,
                    hoverinfo: 'name+x+y',
                    hovertemplate: 'Value: %{y:.4f}<br>Total draw: %{customdata:.4f}',
                };
            }
        );

    const elecSupplyChartData = Object.keys(filteredAndRangedData)
        .filter((key) => elec_supply_stackbars.includes(key))
        .map((key) => {
                return {
                    x: xValues, //columnLabels,
                    y: elec_supply_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                    name: rangedData[key]?.name || key,
                    type: 'bar',
                    marker: getMarker(key),
                    customdata: positiveTotals,
                    hoverinfo: 'x+y+name',
                    hovertemplate: 'Value: %{y:.4f}<br>Total supply: %{customdata:.4f}',
                };
            }
        );

    const heatDrawChartData = Object.keys(filteredAndRangedData)
        .filter((key) => heat_draw_stackbars.includes(key))
        .map((key) => {
                return {
                    x: xValues, //columnLabels,
                    y: heat_draw_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                    name: rangedData[key]?.name || key,
                    type: 'bar',
                    marker: getMarker(key),
                    customdata: negativeTotals,
                    hoverinfo: 'name+x+y',
                    hovertemplate: 'Value: %{y:.4f}<br>Total draw: %{customdata:.4f}',
                };
            }
        );

    const heatSupplyChartData = Object.keys(filteredAndRangedData)
        .filter((key) => heat_supply_stackbars.includes(key))
        .map((key) => {
                return {
                    x: xValues, //columnLabels,
                    y: heat_supply_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                    name: rangedData[key]?.name || key,
                    type: 'bar',
                    marker: getMarker(key),
                    customdata: positiveTotals,
                    hoverinfo: 'x+y+name',
                    hovertemplate: 'Value: %{y:.4f}<br>Total supply: %{customdata:.4f}',
                };
            }
        );

    const elecShortfallChartData = Object.keys(filteredAndRangedData)
        .filter((key) => elec_shortfall_stackbars.includes(key))
        .map((key) => {
                return {
                    x: xValues, //columnLabels,
                    y: elec_shortfall_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                    name: rangedData[key]?.name || key,
                    type: 'bar',
                    marker: getMarker(key),
                    customdata: negativeTotals,
                    hoverinfo: 'name+x+y',
                    hovertemplate: 'Value: %{y:.4f}<br>Total draw: %{customdata:.4f}',
                };
            }
        );

    const heatShortfallChartData = Object.keys(filteredAndRangedData)
        .filter((key) => heat_shortfall_stackbars.includes(key))
        .map((key) => {
                return {
                    x: xValues, //columnLabels,
                    y: heat_shortfall_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                    name: rangedData[key]?.name || key,
                    type: 'bar',
                    marker: getMarker(key),
                    customdata: negativeTotals,
                    hoverinfo: 'name+x+y',
                    hovertemplate: 'Value: %{y:.4f}<br>Total draw: %{customdata:.4f}',
                };
            }
        );

    const elecSurplusChartData = Object.keys(filteredAndRangedData)
        .filter((key) => elec_surplus_stackbars.includes(key))
        .map((key) => {
                return {
                    x: xValues, //columnLabels,
                    y: elec_surplus_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                    name: rangedData[key]?.name || key,
                    type: 'bar',
                    marker: getMarker(key),
                    customdata: positiveTotals,
                    hoverinfo: 'name+x+y',
                    hovertemplate: 'Value: %{y:.4f}<br>Total supply: %{customdata:.4f}',
                };
            }
        );

    const heatSurplusChartData = Object.keys(filteredAndRangedData)
        .filter((key) => heat_surplus_stackbars.includes(key))
        .map((key) => {
                return {
                    x: xValues, //columnLabels,
                    y: heat_surplus_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                    name: rangedData[key]?.name || key,
                    type: 'bar',
                    marker: getMarker(key),
                    customdata: positiveTotals,
                    hoverinfo: 'name+x+y',
                    hovertemplate: 'Value: %{y:.4f}<br>Total supply: %{customdata:.4f}',
                };
            }
        );



    let chartData: any[] = [];
    switch(selectedStackbarGroups) {
        case "all":
            chartData = [
                ...elecSupplyChartData, ...heatSupplyChartData,
                ...elecSurplusChartData, ...heatSurplusChartData,
                ...elecDrawChartData, ...heatDrawChartData,
                ...elecShortfallChartData, ...heatShortfallChartData
            ];
            break;
        case "elec":
            chartData = [
                ...elecSupplyChartData, ...elecSurplusChartData,
                ...elecDrawChartData, ...elecShortfallChartData
            ];
            break;
        case "heat":
            chartData = [
                ...heatSupplyChartData, ...heatSurplusChartData,
                ...heatDrawChartData, ...heatShortfallChartData];
            break;
    }


    // we're using the theme's paper colour for both the plot and paper parts to the plot
    // (this is closer to what plotly does by default and looks a bit better)
    const isDarkMode = useMediaQuery('(prefers-color-scheme: dark)')
    const theme = getAppTheme(isDarkMode);
    const paper_bgcolor = theme.palette.background.paper;
    const plot_bgcolor = theme.palette.background.paper;


    const layout = {
        title: `Half-hourly energy balances across the site`,
        barmode: 'relative',
        xaxis: {title: "Date & Time",
            type: 'date',
            tickformat: "%H:%M",
            dtick: "3600000", // one tick every hour
            range: [
                new Date(xValues[0]).getTime() - 1800000 ,
                new Date(xValues[xValues.length-1]).getTime() + 1800000
            ],
            tickmode: "array",
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
        height: windowWidth * 0.95 * 0.4, // Adjust height as needed
        paper_bgcolor: paper_bgcolor,
        plot_bgcolor: plot_bgcolor,
    }


    return (
        <div style={{ display: 'flex', alignItems: 'flex-start' }}>
            <div style={{width: windowWidth * 0.95}}>
                <Plot data={chartData} layout={layout}/>
            </div>
            <div style={{ marginLeft: '-200px', marginTop: '50px', display: 'flex', flexDirection: 'column' }}>
                <FormControl variant="outlined" size="small" style={{ minWidth: 200 }}>
                    <InputLabel id="chart-select-label">Dataset</InputLabel>
                    <Select
                    labelId="chart-select-label"
                    id="chart-select"
                    value={selectedStackbarGroups}
                    label="Dataset"
                    onChange={(e) => setSelectedStackbarGroups(e.target.value as StackbarOption)}
                    >
                    {stackbarGroups.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                        {option.label}
                        </MenuItem>
                    ))}
                    </Select>
                </FormControl>
            </div>
        </div>
    )
}

import React from "react"
import Plot from "react-plotly.js"

import {color_map, default_positive_stackbars, default_negative_stackbars} from "./GraphConfig";
import {useMediaQuery} from "@mui/material";
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

    // Remove any entries that aren't in default lists; change sign of negative data
    const filteredAndRangedData = Object.fromEntries(
        Object.entries(rangedData)
            .filter(([key]) => default_positive_stackbars.includes(key) || default_negative_stackbars.includes(key))
            .map(([key, value]) =>
                default_negative_stackbars.includes(key) // condition on whether variable is a negative bar (an energy source)
                    ? [key, value.data.map(value => -value)]  // transform if so
                    : [key, value.data]) // otherwise, leave as-is
    );

    // Calculate the negative total (energy draw)
    const negativeTotals = filteredAndRangedData[Object.keys(filteredAndRangedData)[0]].map((_, i) =>
        Object.entries(filteredAndRangedData)
            .filter(([key]) => default_negative_stackbars.includes(key))
            .reduce((sum, [_, arr]) => sum + arr[i], 0)
    );

    // Calculate the positive total (energy supply)
    const positiveTotals = filteredAndRangedData[Object.keys(filteredAndRangedData)[0]].map((_, i) =>
        Object.entries(filteredAndRangedData)
            .filter(([key]) => default_positive_stackbars.includes(key))
            .reduce((sum, [_, arr]) => sum + arr[i], 0)
    );


    const negativeChartData = Object.keys(filteredAndRangedData)
        .filter((key) => default_negative_stackbars.includes(key))
        .map((key) => {
            return {
                    x: xValues, //columnLabels,
                    y: default_negative_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                    name: key,
                    type: 'bar',
                    marker: {color: color_map[key]},
                    customdata: negativeTotals,
                    hoverinfo: 'name+x+y',
                    hovertemplate: 'Value: %{y:.4f}<br>Total draw: %{customdata:.4f}',
            };
        }
    );

    const positiveChartData = Object.keys(filteredAndRangedData)
        .filter((key) => default_positive_stackbars.includes(key))
        .map((key) => {
            return {
                x: xValues, //columnLabels,
                y: default_positive_stackbars.includes(key) ? filteredAndRangedData[key] : undefined,
                name: key,
                type: 'bar',
                marker: {color: color_map[key]},
                customdata: positiveTotals,
                hoverinfo: 'x+y+name',
                hovertemplate: 'Value: %{y:.4f}<br>Total supply: %{customdata:.4f}',
            };
        }
    );

    const chartData = [...negativeChartData, ...positiveChartData];


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
        // responsive: true
    }



    return (
        <div style={{width: windowWidth * 0.95}}>
            <Plot data={chartData} layout={layout}/>
        </div>
    )
}

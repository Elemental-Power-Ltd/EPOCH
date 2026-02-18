import React from "react";
// @ts-ignore
import Plot from "react-plotly.js"
import {Box, GridLegacy as Grid, useTheme} from "@mui/material";

interface yEntry {
    name: string,
    data: number[];
    fullName?: string;
}

interface SiteDataLinePlotProps {
    title: string;
    xData: Date[];
    yData: yEntry[];
    yLabel: string;
}

export const SiteDataLinePlot: React.FC<SiteDataLinePlotProps> = (
    {title, xData, yData, yLabel}) => {

    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';

    // Conditional logic to use the paper colour in dark mode and the default colour in light mode
    const plot_bgcolor = isDarkMode
        ? theme.palette.background.paper
        : theme.palette.background.default;
    const paper_bgcolor = isDarkMode
        ? theme.palette.background.paper
        : theme.palette.background.default;

    // add some extra spacing in a few places when we have a lot of entries to plot
    const manyLines = yData.length > 8

    return (
        <Grid item xs={12} md={6}>
            <Box sx={{width: "100%", height: manyLines ? "60vh" : "50vh"}}>
                <Plot
                    data={yData.map((y) => (
                        {
                            x: xData,
                            y: y.data,
                            type: 'scatter',
                            mode: 'lines',
                            name: y.name,
                            meta: y.fullName ?? y.name,
                            hovertemplate: `%{meta}<br>${yLabel}: %{y:.2f}<extra></extra>`
                        }
                    ))}
                    layout={{
                        title: title,
                        xaxis: {
                            title: 'Time',
                            range: [xData[0], xData[xData.length - 1]]
                        },
                        yaxis: {title: yLabel},
                        paper_bgcolor: paper_bgcolor,
                        plot_bgcolor: plot_bgcolor,
                        autosize: true,
                        legend: {
                            orientation: 'h',
                            yanchor: 'top',
                            y: -0.2,
                            xanchor: 'left',
                            x: 0,
                            font: {size: manyLines ? 10 : 12},
                        },
                        margin: {
                            t: 60,  // padding for the title
                            l: 40,  // padding for the y axis
                            r: 0,
                            b: manyLines ? 140 : 110  // padding for the legend
                        },
                        font: {color: theme.palette.text.primary},
                        hovermode: 'x unified',
                        uirevision: true,
                    }}
                    useResizeHandler={true}
                    style={{width: "100%", height: "100%"}}
                    config={{
                        responsive: true,
                        displayModeBar: false
                    }}
                />
            </Box>
        </Grid>
    )
}
import React from "react";
import Plot from "react-plotly.js"
import {Box, Grid, useMediaQuery} from "@mui/material";
import {getAppTheme} from "../../Colours";

interface yEntry {
    name: string,
    data: number[];
}

interface SiteDataLinePlotProps {
    title: string;
    xData: Date[];
    yData: yEntry[];
    yLabel: string;
}

export const SiteDataLinePlot: React.FC<SiteDataLinePlotProps> = (
    {title, xData, yData, yLabel}) => {

    const isDarkMode = useMediaQuery('(prefers-color-scheme: dark)')
    const theme = getAppTheme(isDarkMode);
    const paper_bgcolor = theme.palette.background.paper;
    const plot_bgcolor = theme.palette.background.paper;

    return (
        <Grid item xs={12} md={6}>
            <Box sx={{width: "100%", height: "50vh"}}>
                <Plot
                    data={yData.map((y) => (
                        {
                            x: xData,
                            y: y.data,
                            type: 'scatter',
                            mode: 'lines',
                            name: y.name
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
                            yanchor: 'bottom',
                            y: 1.0,
                            xanchor: 'center',
                            x: 0.5
                        },
                        margin: {
                            t: 100,  // We need a high top-margin to prevent the Title and Legend overlapping
                            l: 40,  // Left margin prevents the Y-axis labels overlapping with the chart
                            r: 20,
                            b: 60  // bottom margin prevent the x-axis overlapping with the chart
                        },
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
import React, {useState} from "react";
import Plot from "react-plotly.js"
import {FormControl, InputLabel, Select, MenuItem, useMediaQuery, ListSubheader} from "@mui/material"

import {color_map, lineChartDefaults} from "./GraphConfig";
import {getAppTheme} from "../../Colours";
import {ensureContrastHue} from "./GraphUtils";
import {DataAnnotationMap} from "./TimeSeriesAnnotations";

interface LineChartPanelProps {
    rangedData: DataAnnotationMap;
    xValues: Date[];
    windowWidth: number;
}


export const LineChartPanels: React.FC<LineChartPanelProps> = ({
    rangedData, xValues, windowWidth
}) => {

    // Grouped dropdown options for line charts
    const inputOptions = Object.keys(rangedData)
        .filter(key => rangedData[key].type === 'Input')
        .map(key => ({value: key, label: rangedData[key].name}));

    const outputOptions = Object.keys(rangedData)
        .filter(key => rangedData[key].type === 'Output')
        .map(key => ({value: key, label: rangedData[key].name}));

    const [panelSelections, setPanelSelections] = useState(lineChartDefaults);

    const handleSelectChange = (panelIndex, selectedVar, isVar1) => {
        setPanelSelections((prev) =>
            prev.map((panel, idx) =>
                idx === panelIndex
                    ? {...panel, [isVar1 ? 'var1' : 'var2']: selectedVar}
                    : panel
            )
        );
    };

    // we're using the theme's paper colour for both the plot and paper parts to the plot
    // (this is closer to what plotly does by default and looks a bit better)
    const isDarkMode = useMediaQuery('(prefers-color-scheme: dark)')
    const theme = getAppTheme(isDarkMode);
    const paper_bgcolor = theme.palette.background.paper;
    const plot_bgcolor = theme.palette.background.paper;


    return (
        <div id="panel-charts" style={{//border: '2px dotted rgb(96 139 168)',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '20px',
            marginTop: '20px',
            width: 0.95 * windowWidth, // width of grid
            boxSizing: 'border-box',
        }}>
            {panelSelections.map((panel, index) => (
                <div key={index} style={{
                    border: '3px solid rgb(7, 96, 64)',
                    borderRadius: '10px',
                    padding: '1.5%'
                }}>
                    {/* Dropdowns for Variable Selection */}
                    <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '2px'}}>
                        <FormControl sx={{minWidth: 120}}>
                            <InputLabel id={`var1-label-${index}`}>Variable 1</InputLabel>
                            <Select
                                labelId={`var1-label-${index}`}
                                id={`var1-select-${index}`}
                                label="Variable 1"
                                value={panel.var1}
                                onChange={(e) => handleSelectChange(index, e.target.value, true)}
                            >
                                {inputOptions.length > 0 && <ListSubheader>Inputs</ListSubheader>}
                                {inputOptions.map((option) => (
                                    <MenuItem key={option.value} value={option.value}>
                                        {option.label}
                                    </MenuItem>
                                ))}
                                {outputOptions.length > 0 && <ListSubheader>Outputs</ListSubheader>}
                                {outputOptions.map((option) => (
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
                                {inputOptions.length > 0 && <ListSubheader>Inputs</ListSubheader>}
                                {inputOptions.map((option) => (
                                    <MenuItem key={option.value} value={option.value}>
                                        {option.label}
                                    </MenuItem>
                                ))}
                                {outputOptions.length > 0 && <ListSubheader>Outputs</ListSubheader>}
                                {outputOptions.map((option) => (
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
                                x: xValues, // Shared x-axis: filtered date range
                                y: rangedData[panel.var1]?.data || [],
                                name: panel.var1,
                                type: 'scatter',
                                mode: 'lines',
                                line: {
                                    color: (() => {
                                        const color1 = color_map[panel.var1] || '#1f77b4';
                                        const color2 = color_map[panel.var2] || '#d96b09';
                                        const result = ensureContrastHue(color1, color2, isDarkMode);
                                        return result;
                                    })()
                                },  // Default to blue if not in map
                            },
                            {
                                x: xValues,
                                y: rangedData[panel.var2]?.data || [],
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
                                    const result = ensureContrastHue(color1, color2, isDarkMode);
                                    const resulting_text = `<span style="color:${result};">${panel.var1}</span> vs <span style="color:${color2};">${panel.var2}</span>`
                                    return resulting_text;
                                })()
                            },
                            xaxis: {title: 'Date & Time'},
                            yaxis: {title: 'Value'},
                            margin: {l: 65, r: 65, t: 50, b: 50},
                            autosize: false, // Disable autosize
                            width: windowWidth * 0.45, // 45% of the window width per panel
                            height: windowWidth * 0.45 * 0.6, // Adjust height as needed
                            showlegend: false,
                            paper_bgcolor: paper_bgcolor,
                            plot_bgcolor: plot_bgcolor,
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
    );
}

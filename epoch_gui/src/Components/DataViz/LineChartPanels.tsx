import React, {useState} from "react";
// @ts-ignore
import Plot from "react-plotly.js"
import {FormControl, InputLabel, Select, MenuItem, ListSubheader, useTheme} from "@mui/material"

import {color_map, lineChartDefaults} from "./GraphConfig";
import {ensureContrastHue} from "./GraphUtils";
import {DataAnnotationMap} from "./TimeSeriesAnnotations";

interface LineChartPanelProps {
    rangedData: DataAnnotationMap;
    xValues: Date[];
    windowWidth: number;
}

interface PanelSelection {
    var1: string;
    var2: string;
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

    const handleSelectChange = (panelIndex: number, selectedVar: string, isVar1: boolean) => {
        setPanelSelections((prev) =>
            prev.map((panel, idx) =>
                idx === panelIndex
                    ? {...panel, [isVar1 ? 'var1' : 'var2']: selectedVar}
                    : panel
            )
        );
    };


    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';

    // Conditional logic to use the paper colour in dark mode and the default colour in light mode
    const plot_bgcolor = isDarkMode
        ? theme.palette.background.paper
        : theme.palette.background.default;
    const paper_bgcolor = isDarkMode
        ? theme.palette.background.paper
        : theme.palette.background.default;


    const buildPlotData = (
        var1: string, var2: string,
        var1Name: string, var2Name: string,
        var1Color: string, var2Color: string,
        differentUnits: boolean
    ) => {
        return [
            {
                x: xValues,
                y: rangedData[var1]?.data || [],
                name: var1Name,
                type: 'scatter',
                mode: 'lines',
                line: { color: var1Color },
                yaxis: 'y' // var1 always on the left axis
            },
            {
                x: xValues,
                y: rangedData[var2]?.data || [],
                name: var2Name,
                type: 'scatter',
                mode: 'lines',
                line: { color: var2Color },
                // Use y2 if units differ, else use y
                yaxis: differentUnits ? 'y2' : 'y'
            },
        ];
    };

    const buildPlotLayout = (
        var1Name: string,
        var2Name: string,
        var1Units: string | undefined,
        var2Units: string | undefined,
        var1Color: string,
        var2Color: string,
        differentUnits: boolean
    ) => {
        // Build the HTML for the chart title
        const titleHTML = `<span style="color:${var1Color};">${var1Name}</span>`
            + ` vs <span style="color:${var2Color};">${var2Name}</span>`;

        return {
            title: { text: titleHTML },
            xaxis: { title: 'Date & Time' },
            yaxis: { title: var1Units || 'Value' },
            // If the units differ, define a second y-axis on the right
            ...(differentUnits && {
                yaxis2: {
                    title: var2Units || 'Value',
                    overlaying: 'y',
                    side: 'right'
                }
            }),
            margin: { l: 65, r: 65, t: 50, b: 50 },
            autosize: false, // Disable autosize
            width: windowWidth * 0.45, // 45% of the window width per panel
            height: windowWidth * 0.45 * 0.6, // Adjust height as needed
            showlegend: false,
            paper_bgcolor: paper_bgcolor,
            plot_bgcolor: plot_bgcolor,
            font: {color: theme.palette.text.primary},
        };
    };

    // Render each panel
    const renderPanel = (panel: PanelSelection, index: number) => {
        // Check units to determine if we need a second y-axis
        const var1Units = rangedData[panel.var1]?.units;
        const var2Units = rangedData[panel.var2]?.units;
        const differentUnits = var1Units && var2Units && var1Units !== var2Units;

        // Get display names
        const var1Name = rangedData[panel.var1]?.name || panel.var1;
        const var2Name = rangedData[panel.var2]?.name || panel.var2;

        // Choose colors
        const defaultColor1 = '#1f77b4'; // Fallback for var1
        const defaultColor2 = '#d96b09'; // Fallback for var2
        const color1 = color_map[panel.var1 as keyof typeof color_map] || defaultColor1;
        const color2 = color_map[panel.var2 as keyof typeof color_map] || defaultColor2;
        // Ensure var1 color contrasts with var2 color in dark mode
        const var1Color = ensureContrastHue(color1, color2, isDarkMode);
        const var2Color = color2; // var2 just uses the default or mapped color

        return (
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
                    data={buildPlotData(
                        panel.var1, panel.var2,
                        var1Name, var2Name,
                        var1Color, var2Color,
                        !!differentUnits
                    )}
                    layout={buildPlotLayout(
                        var1Name,
                        var2Name,
                        var1Units,
                        var2Units,
                        var1Color,
                        var2Color,
                        !!differentUnits
                    )}
                />
            </div>
        );
    };

    return (
        <div id="panel-charts" style={{//border: '2px dotted rgb(96 139 168)',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '20px',
            marginTop: '20px',
            width: 0.95 * windowWidth, // width of grid
            boxSizing: 'border-box',
        }}>
            {panelSelections.map(renderPanel)}
        </div>
    );
};

import React, {useMemo, useState} from "react";
// @ts-ignore
import Plot from "react-plotly.js";
import {calculatePiecewiseCosts} from "./PiecewiseEditor.tsx";
import {PiecewiseCostModel} from "./Types.ts";
import {useTheme} from "@mui/material/styles";


type Props = {
    model: PiecewiseCostModel;
    unitHint?: string;
};

export const CostModelPlot: React.FC<Props> = ({model, unitHint}) => {
    const [exampleUnitsInput, setExampleUnitsInput] = useState<string>("");

    // Parse & sanitize the example field
    const exampleUnits = useMemo(() => {
        const n = parseFloat(exampleUnitsInput);
        return Number.isFinite(n) && n >= 0 ? n : undefined;
    }, [exampleUnitsInput]);

    // Build piecewise line points
    const {xs, ys} = useMemo(() => {
        const xs: number[] = [];
        const ys: number[] = [];

        // Start at x=0
        let prevUpper = 0;
        let total = model.fixed_cost;

        xs.push(0);
        ys.push(total);

        for (const seg of model.segments) {
            // Move horizontally to seg.upper at current segment rate
            total += (seg.upper - prevUpper) * seg.rate;
            xs.push(seg.upper);
            ys.push(total);
            prevUpper = seg.upper;
        }

        // extend the X-axis to either 50% beyond the last segment or 10% beyond the example value
        const lastUpper = prevUpper;
        const baseMax = lastUpper > 0 ? lastUpper * 1.5 : 10;
        const maxX = Math.max(baseMax, exampleUnits !== undefined ? exampleUnits * 1.1 : 0);

        // Add a terminal point into the final rate region
        const finalY = total + Math.max(0, maxX - lastUpper) * model.final_rate;
        xs.push(maxX);
        ys.push(finalY);

        return {xs, ys, inferredMaxX: xs[xs.length - 1]};
    }, [model, exampleUnits]);

    // Build traces
    const traces: any[] = [
        {
            x: xs,
            y: ys,
            mode: "lines",
            name: "Total Cost (£)",
            hovertemplate: "Units: %{x}<br>Cost: £%{y:.2f}<extra></extra>",
        },
    ];

    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';

    // Conditional logic to use the paper colour in dark mode and the default colour in light mode
    const plot_bgcolor = isDarkMode
        ? theme.palette.background.paper
        : theme.palette.background.default;
    const paper_bgcolor = isDarkMode
        ? theme.palette.background.paper
        : theme.palette.background.default;


    // If the example field has a value, add an intercept marker
    let interceptY: number | undefined;
    if (exampleUnits !== undefined) {
        interceptY = calculatePiecewiseCosts(model, exampleUnits);
        traces.push({
            x: [exampleUnits],
            y: [interceptY],
            mode: "markers",
            name: "Intercept",
            marker: {size: 10},
            hovertemplate: "Units: %{x}<br>Cost: %{y:.2f}<extra></extra>",
        });
    }

    const shapes =
        exampleUnits !== undefined && interceptY !== undefined
            ? [
                // vertical guide
                {
                    type: "line",
                    xref: "x",
                    yref: "paper",
                    x0: exampleUnits,
                    x1: exampleUnits,
                    y0: 0,
                    y1: 1,
                    line: {dash: "dot"},
                },
                // horizontal guide
                {
                    type: "line",
                    xref: "paper",
                    yref: "y",
                    x0: 0,
                    x1: 1,
                    y0: interceptY,
                    y1: interceptY,
                    line: {dash: "dot"},
                },
            ]
            : [];

    return (
        <div style={{width: "100%", maxWidth: 900}}>
            <label style={{display: "block", marginBottom: 8}}>
                Example value:
                <input
                    type="number"
                    min={0}
                    step="1"
                    value={exampleUnitsInput}
                    onChange={(e) => setExampleUnitsInput(e.target.value)}
                    placeholder="Enter a value to show costs"
                    style={{
                        marginLeft: 8,
                        padding: "6px 8px",
                        borderRadius: 6,
                        border: "1px solid #ccc",
                        width: 220,
                    }}
                />
                {unitHint ?? "Units"}
            </label>

            <Plot
                data={traces}
                layout={{
                    xaxis: {title: unitHint ?? "Units", rangemode: "tozero"},
                    yaxis: {title: "Total Cost (£)", rangemode: "tozero"},
                    margin: {l: 60, r: 20, t: 50, b: 50},
                    shapes,
                    hovermode: "x unified",
                    paper_bgcolor: paper_bgcolor,
                    plot_bgcolor: plot_bgcolor,
                }}
                style={{width: "100%", height: 480}}
                useResizeHandler
                config={{displayModeBar: true, responsive: true}}
            />
        </div>
    );
};

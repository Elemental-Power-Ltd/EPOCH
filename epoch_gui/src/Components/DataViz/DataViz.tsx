import React, {useEffect, useState} from "react";
import {Alert, Button, Collapse, Grid, IconButton} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import dayjs, {Dayjs} from 'dayjs';

import {NonNullReportDataType, ReportDataType, SimulationResult} from "../../Models/Endpoints";
import {onClickDownloadReportData} from "../../util/MakeCSV";
import {DateRangeControls} from "./DateRangeControls";
import {StackedBarChart} from "./StackedBarChart";
import {LineChartPanels} from "./LineChartPanels";
import {removeEmptyVectors} from "./GraphUtils";
import {DataAnnotationMap, getAnnotatedSeries} from "./TimeSeriesAnnotations";
import {DayOfInterestSelector} from "./DayOfInterestSelector.tsx";
import {ExplainerDialog} from "../Explainer/ExplainerDialog.tsx";
import {DataVizTips} from "./ExplainerTips.ts";

interface DataVizProps {
    result: SimulationResult;
    // We present slightly different styling for the Informed embed
    isInformedEmbed?: boolean;
}

const DataVizContainer: React.FC<DataVizProps> = ({ result, isInformedEmbed = false }) => {
    if (result.report_data === null) {
        return <Alert severity="error">Result contains no time series!</Alert>
    }

    const reportData = removeEmptyVectors(getNonNullReportData(result.report_data));

    // Set const values for the assumed first date and sampling frequency in rawData
    const initialDatetime = dayjs("2022-01-01T00:00:00Z"); // Example default initial datetime
    const finalDatetime = initialDatetime.add(1, 'year');
    const dataPeriodInMinutes = 30;
    const samplingFrequencySeconds = 1 / (dataPeriodInMinutes * 60); // Example: 1 sample per half hour
    const samplingFrequencyMs = samplingFrequencySeconds / 1000;

    // Initial states - variables for filtering data
    const [selectedStartDatetime, setSelectedStartDatetime] = useState<Dayjs|null>(initialDatetime);
    const [daysToKeep, setDaysToKeep] = useState(1);

    const fullTimeSeries = getAnnotatedSeries(result.task_data, result.site_data!, reportData);
    const [rangedData, setRangedData] = useState<DataAnnotationMap>(fullTimeSeries);

    // EPOCH GUI shows line charts by default, Informed Embed does not
    const [embedOpen, setEmbedOpen] = useState(false);
    const showLineCharts = isInformedEmbed ? embedOpen : true;

    // Initial states - variable for reacting to browser window size
    const [windowWidth, setWindowWidth] = useState(window.innerWidth);

    const [showExplainer, setShowExplainer] = useState<boolean>(false);

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

        const filtered: DataAnnotationMap = Object.fromEntries(
            Object.entries(fullTimeSeries).map(([key,value]) =>
                [key, {...value, data: value.data.slice(startIndex, endIndex + 1)}]
        ));

        setRangedData(filtered);
    }, [selectedStartDatetime, daysToKeep]);


    // We add an offset to the X values so that the bars are centred on the midpoint of each timerange
    // ie centred around 00:15 rather than 00:00 for the first entry in the day
    const offset_to_centre = dataPeriodInMinutes / 2
    const x_hh = Array.from({ length: daysToKeep * 48 }, (_, i) =>
        dayjs(selectedStartDatetime).add(i*30 + offset_to_centre, 'minute').toDate()
    )


    // Update window width on resize
    useEffect(() => {
        const handleResize = () => setWindowWidth(Math.min(window.innerWidth,1800));
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);
    }, []);


    return (
        <div style={{
            display: 'flex', flexDirection: 'column',
            margin: '1em 0 0 0', width: '100%', alignItems: 'center', justifySelf: 'center',
            boxSizing: 'border-box',
            position: 'relative',
        }}
        >
            <IconButton
                aria-label="Open explainer"
                onClick={() => setShowExplainer(true)}
                style={{position: 'absolute', top: 4, right: 4}}
            >
                <HelpOutlineIcon/>
            </IconButton>


            <DateRangeControls
                selectedStartDatetime={selectedStartDatetime}
                setSelectedStartDatetime={setSelectedStartDatetime}
                daysToKeep={daysToKeep}
                setDaysToKeep={setDaysToKeep}
                minDateTime={initialDatetime}
                maxDateTime={finalDatetime}
            />

            <StackedBarChart rangedData={rangedData} xValues={x_hh} windowWidth={windowWidth}/>

            {result.days_of_interest && (
                <Grid item>
                    <DayOfInterestSelector
                        daysOfInterest={result.days_of_interest}
                        setSelectedStartDatetime={setSelectedStartDatetime}
                        setDaysToKeep={setDaysToKeep}
                    />
                </Grid>
            )}

            <ExplainerDialog
                open={showExplainer}
                tips={DataVizTips}
                onClose={()=>setShowExplainer(false)}
                dialogTitle={"Energy Flows"}
                maxWidth="xl"
            />

            {isInformedEmbed && (
                <Button
                    variant="text"
                    onClick={() => setEmbedOpen(v => !v)}
                    startIcon={
                        <ExpandMoreIcon
                            style={{
                                transform: showLineCharts ? 'rotate(180deg)' : 'rotate(0deg)',
                                transition: 'transform 200ms'
                            }}
                        />
                    }
                    aria-expanded={showLineCharts}
                    aria-controls="line-chart-panels"
                    style={{ marginTop: '0.5em' }}
                >
                    {showLineCharts ? 'Hide line plots' : 'Show line plots'}
                </Button>
            )}

            {isInformedEmbed ? (
                <Collapse in={showLineCharts} unmountOnExit>
                    <div id="line-chart-panels">
                        <LineChartPanels rangedData={rangedData} xValues={x_hh} windowWidth={windowWidth} />
                    </div>
                </Collapse>
            ) : (
                <LineChartPanels rangedData={rangedData} xValues={x_hh} windowWidth={windowWidth} />
            )}

            {!isInformedEmbed &&
                <Button
                    variant="outlined"
                    onClick={() => onClickDownloadReportData(reportData)}
                    startIcon={<DownloadIcon/>}
                    style={{marginTop: '1em'}}
                >
                    Download CSV
                </Button>
            }
        </div>
    );
}

export default DataVizContainer


const getNonNullReportData = (reportData: ReportDataType | null): NonNullReportDataType => {
    if (!reportData) return {};
    return Object.fromEntries(
        Object.entries(reportData).filter(
            ([, value]) => value !== null
        ) as [string, number[]][]
    );
};

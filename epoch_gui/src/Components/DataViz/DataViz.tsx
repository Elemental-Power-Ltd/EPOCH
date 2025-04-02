import React, {useEffect, useState} from "react";
import {Button} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import dayjs, {Dayjs} from 'dayjs';

import {SimulationResult} from "../../Models/Endpoints";
import {onClickDownloadReportData} from "../../util/MakeCSV";
import {DateRangeControls} from "./DateRangeControls";
import {StackedBarChart} from "./StackedBarChart";
import {LineChartPanels} from "./LineChartPanels";
import {removeEmptyVectors} from "./GraphUtils";
import {DataAnnotationMap, getAnnotatedSeries} from "./TimeSeriesAnnotations";

interface DataVizProps {
    result: SimulationResult
}

const DataVizContainer: React.FC<DataVizProps> = ({result}) => {

    const reportData = removeEmptyVectors(result.report_data!);

    // Set const values for the assumed first date and sampling frequency in rawData
    const initialDatetime = dayjs("2022-01-01T00:00:00Z"); // Example default initial datetime
    const finalDatetime = initialDatetime.add(1, 'year');
    const dataPeriodInMinutes = 30;
    const samplingFrequencySeconds = 1 / (dataPeriodInMinutes * 60); // Example: 1 sample per half hour
    const samplingFrequencyMs = samplingFrequencySeconds / 1000;

    // Initial states - variables for filtering data
    const [selectedStartDatetime, setSelectedStartDatetime] = useState<Dayjs|null>(initialDatetime);
    const [daysToKeep, setDaysToKeep] = useState(1);

    const nonNullReportData = result.report_data || {};

    const fullTimeSeries = getAnnotatedSeries(result.task_data, result.site_data!, nonNullReportData);
    const [rangedData, setRangedData] = useState<DataAnnotationMap>(fullTimeSeries);

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
        <div style={{//border: '2px dotted rgb(96 139 168)',
            display: 'flex', flexDirection: 'column',
            margin: '1em 0 0 0', width: '100%', alignItems: 'center', justifySelf: 'center',
            boxSizing: 'border-box'
        }}
        >
            <DateRangeControls
                selectedStartDatetime={selectedStartDatetime}
                setSelectedStartDatetime={setSelectedStartDatetime}
                daysToKeep={daysToKeep}
                setDaysToKeep={setDaysToKeep}
                minDateTime={initialDatetime}
                maxDateTime={finalDatetime}
            />

            <StackedBarChart rangedData={rangedData} xValues={x_hh} windowWidth={windowWidth}/>
            <LineChartPanels rangedData={rangedData} xValues={x_hh} windowWidth={windowWidth}/>

            <Button
                variant="outlined"
                onClick={() => onClickDownloadReportData(reportData)}
                startIcon={<DownloadIcon/>}
                style={{marginTop: '1em'}}
            >
                Download CSV
            </Button>
        </div>
    );
}

export default DataVizContainer

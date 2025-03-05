import React, {useEffect, useState} from "react";
import {Alert, Box, Button, Container, Grid} from "@mui/material";
import dayjs, {Dayjs} from "dayjs";

import {EpochSiteData} from "../../Models/Endpoints";
import {SiteDataLinePlot} from "./SiteDataLinePlot";
import {DateRangeControls} from "../DataViz/DateRangeControls";
import DownloadIcon from "@mui/icons-material/Download";
import {downloadCSV, downloadJSON} from "./donwloadSiteData";

interface SiteDataViewerProps {
    siteData: EpochSiteData
}

export const SiteDataViewer: React.FC<SiteDataViewerProps> = ({siteData}) => {
    const initialDatetime = dayjs(siteData.start_ts);
    const dataPeriodInMinutes = 30;
    const samplingFrequencySeconds = 1 / (dataPeriodInMinutes * 60); // Example: 1 sample per half hour
    const samplingFrequencyMs = samplingFrequencySeconds / 1000;

    const [selectedStartDatetime, setSelectedStartDatetime] = useState<Dayjs | null>(initialDatetime);
    const [daysToKeep, setDaysToKeep] = useState(1);


    const initialTimestampMs = initialDatetime.valueOf();
    const startTimestampMs = selectedStartDatetime!.valueOf();
    const endTimestampMs = startTimestampMs + daysToKeep * 24 * 60 * 60 * 1000 - 1;

    const startIndex = Math.floor((startTimestampMs - initialTimestampMs) * samplingFrequencyMs);
    const endIndex = Math.floor((endTimestampMs - initialTimestampMs) * samplingFrequencyMs);

    const rangedSiteData: EpochSiteData = {
        start_ts: siteData.start_ts,
        end_ts: siteData.end_ts,

        building_eload: siteData.building_eload.slice(startIndex, endIndex + 1),
        building_hload: siteData.building_hload.slice(startIndex, endIndex + 1),
        ev_eload: siteData.ev_eload.slice(startIndex, endIndex + 1),
        dhw_demand: siteData.dhw_demand.slice(startIndex, endIndex + 1),
        air_temperature: siteData.air_temperature.slice(startIndex, endIndex + 1),
        grid_co2: siteData.grid_co2.slice(startIndex, endIndex + 1),
        solar_yields: siteData.solar_yields.map((solar) => solar.slice(startIndex, endIndex + 1)),
        import_tariffs: siteData.import_tariffs.map((tariff) => tariff.slice(startIndex, endIndex + 1)),
        fabric_interventions: siteData.fabric_interventions.map((fabric => ({
            ...fabric, reduced_hload: fabric.reduced_hload.slice(startIndex, endIndex + 1),
        }))),
        ashp_input_table: siteData.ashp_input_table,
        ashp_output_table: siteData.ashp_output_table
    };

    // We add an offset to the X values so that the bars are centred on the midpoint of each timerange
    // ie centred around 00:15 rather than 00:00 for the first entry in the day
    const offset_to_centre = dataPeriodInMinutes / 2
    const x_hh = Array.from({length: daysToKeep * 48}, (_, i) =>
        dayjs(selectedStartDatetime).add(i * 30 + offset_to_centre, 'minute').toDate()
    );

    const handleDownloadCSV = () => {downloadCSV(siteData)};
    const handleDownloadJSON = () => {downloadJSON(siteData)};


    return (
        <Box sx={{marginTop: "2rem"}}>
            <DateRangeControls
                selectedStartDatetime={selectedStartDatetime}
                setSelectedStartDatetime={setSelectedStartDatetime}
                daysToKeep={daysToKeep}
                setDaysToKeep={setDaysToKeep}
            />

            <Grid container spacing={1}>

                <SiteDataLinePlot
                    title={"Electrical Loads"}
                    xData={x_hh}
                    yData={[
                        {name: "Building Load", data: rangedSiteData.building_eload},
                        {name: "EV Load", data: rangedSiteData.ev_eload}
                    ]}
                    yLabel={"Energy (kWh)"}
                />

                <SiteDataLinePlot
                    title={"Heat Loads"}
                    xData={x_hh}
                    yData={[
                        {name: "Baseline Heat Load", data: rangedSiteData.building_hload},
                        {name: "DHW Demand", data: rangedSiteData.dhw_demand},
                        ...rangedSiteData.fabric_interventions.map((intervention, index) => (
                            {name: `Reduced Heat Load (${index + 1}`, data: intervention.reduced_hload}
                        ))
                    ]}
                    yLabel={"Energy (kWh)"}
                />

                <SiteDataLinePlot
                    title={"Solar Yields"}
                    xData={x_hh}
                    yData={rangedSiteData.solar_yields.map((solar, index) => (
                        {name: `Solar Yield ${index + 1}`, data: solar}
                    ))}
                    yLabel={"Energy (kWh)"}
                />

                <SiteDataLinePlot
                    title={"Import Tariffs"}
                    xData={x_hh}
                    yData={rangedSiteData.import_tariffs.map((tariff, index) => (
                        {name: `Import Tariff ${index + 1}`, data: tariff}
                    ))}
                    yLabel={"£/kWh"}
                />

                <SiteDataLinePlot
                    title={"Air Temperature"}
                    xData={x_hh}
                    yData={[
                        {name: "Air Temperature", data: rangedSiteData.air_temperature},
                    ]}
                    yLabel={"Temperature (°C)"}
                />

                <SiteDataLinePlot
                    title={"Grid CO₂ Emissions Intensity"}
                    xData={x_hh}
                    yData={[
                        {name: "Grid Intensity", data: rangedSiteData.grid_co2},
                    ]}
                    yLabel={"%"}
                />
            </Grid>

            <Container maxWidth={"sm"}>
                <Button variant="outlined" onClick={handleDownloadJSON} startIcon={<DownloadIcon/>}>
                    JSON
                </Button>
                <Button variant="outlined" onClick={handleDownloadCSV} startIcon={<DownloadIcon/>}>
                    CSV
                </Button>
            </Container>
        </Box>
    )
}

// this is a placeholder
// we don't currently return enough information to distinguish between
//  - an error due to no datasets (the intended case for this)
//  - some other server/network error
const NoSiteDataToView = () => {

}

export const ErrorLoadingSiteData = () => (
    <Container maxWidth={"sm"} sx={{padding: "1em"}}>
        <Alert severity="error">Failed to load data for this site.</Alert>
    </Container>
)

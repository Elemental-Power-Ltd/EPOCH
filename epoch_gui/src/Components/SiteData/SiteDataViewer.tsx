import React, {useState} from "react";
import {Alert, Box, Button, Container, Grid, Typography} from "@mui/material";
import dayjs, {Dayjs} from "dayjs";

import {BundleHint, FabricIntervention, EpochSiteData} from "../../Models/Endpoints";
import {SiteDataLinePlot} from "./SiteDataLinePlot";
import {DateRangeControls} from "../DataViz/DateRangeControls";
import DownloadIcon from "@mui/icons-material/Download";
import {downloadCSV, downloadJSON} from "./donwloadSiteData";
import {aggregateSiteData} from "./aggregateSiteData";
import {TaskDataViewer} from "../TaskDataViewer/TaskDataViewer.tsx";
import {snakeToDisplayName} from "../../util/displayFunctions.ts";
import {HintViewer} from "../Bundles/HintViewer.tsx";

interface SiteDataViewerProps {
    siteData: EpochSiteData
    hints: BundleHint | null
}

export const SiteDataViewer: React.FC<SiteDataViewerProps> = ({siteData, hints}) => {

    const initialDatetime = dayjs(siteData.start_ts);
    const finalDatetime = dayjs(siteData.end_ts);

    const [selectedStartDatetime, setSelectedStartDatetime] = useState<Dayjs | null>(initialDatetime);
    const [daysToKeep, setDaysToKeep] = useState(1);

    // if the DaysToKeep is monthly or higher, then we plot daily aggregate data instead of half hourly
    const usingAggregates = daysToKeep >= 30;
    const selectedSiteData = usingAggregates ? aggregateSiteData(siteData) : siteData;
    const length = selectedSiteData.building_eload.length;

    const dataPeriodInSeconds = (finalDatetime.unix() - initialDatetime.unix()) / length;
    const samplingFrequencySeconds = 1 / (dataPeriodInSeconds); // Example: 1 sample per half hour
    const samplingFrequencyMs = samplingFrequencySeconds / 1000;


    const initialTimestampMs = initialDatetime.valueOf();
    const startTimestampMs = selectedStartDatetime!.valueOf();
    const endTimestampMs = startTimestampMs + daysToKeep * 24 * 60 * 60 * 1000 - 1;

    const startIndex = Math.floor((startTimestampMs - initialTimestampMs) * samplingFrequencyMs);
    const endIndex = Math.floor((endTimestampMs - initialTimestampMs) * samplingFrequencyMs);

    const rangedSiteData: EpochSiteData = {
        start_ts: selectedSiteData.start_ts,
        end_ts: selectedSiteData.end_ts,
        baseline: selectedSiteData.baseline,

        building_eload: selectedSiteData.building_eload.slice(startIndex, endIndex + 1),
        building_hload: selectedSiteData.building_hload.slice(startIndex, endIndex + 1),
        ev_eload: selectedSiteData.ev_eload.slice(startIndex, endIndex + 1),
        dhw_demand: selectedSiteData.dhw_demand.slice(startIndex, endIndex + 1),
        air_temperature: selectedSiteData.air_temperature.slice(startIndex, endIndex + 1),
        grid_co2: selectedSiteData.grid_co2.slice(startIndex, endIndex + 1),
        solar_yields: selectedSiteData.solar_yields.map((solar) => solar.slice(startIndex, endIndex + 1)),
        import_tariffs: selectedSiteData.import_tariffs.map((tariff) => tariff.slice(startIndex, endIndex + 1)),
        fabric_interventions: selectedSiteData.fabric_interventions.map((fabric => ({
            ...fabric, reduced_hload: fabric.reduced_hload.slice(startIndex, endIndex + 1),
        }))),
        ashp_input_table: selectedSiteData.ashp_input_table,
        ashp_output_table: selectedSiteData.ashp_output_table
    };

    // We add an offset to the X values so that the bars are centred on the midpoint of each timerange
    // ie centred around 00:15 rather than 00:00 for the first entry in the day
    const offsetToCentreSeconds = 0.5 * dataPeriodInSeconds
    const x_hh = Array.from({length: endIndex + 1 - startIndex}, (_, i) =>
        dayjs(selectedStartDatetime).add(i * dataPeriodInSeconds + offsetToCentreSeconds, 'second').toDate()
    );

    const handleDownloadCSV = () => {downloadCSV(siteData)};
    const handleDownloadJSON = () => {downloadJSON(siteData)};

    // Some of the fabric interventions can be incredibly long.
    // This is a non-exhaustive list to reduce some of the common ones to shorter descriptions
    const shortFabricNames: Readonly<Record<string, string>> = {
        "Insulation to ceiling void": "Ceiling",
        "Replacement External Windows": "Windows",
        "Air tightness to external doors and windows": "Air Tightness",
        "External Insulation to external cavity wall": "External Insulation"
    }

    const tryPatchFabricHint = (intervention: FabricIntervention, index: number) => {
        const defaultLabel = {name: `Reduced Heat Load (${index + 1}`, data: intervention.reduced_hload};
        if (hints === null) {
            return defaultLabel;
        }
        if (hints.heating === null || hints.heating.length < index + 1) {
            console.error("Bundle Heating does not match Fabric Interventions!");
            return defaultLabel;
        }
        const hintedName = hints.heating[index + 1].interventions
            .map((intervention) => shortFabricNames[intervention] ?? intervention)
            .map((intervention) => snakeToDisplayName(intervention))
            .join(' • ');
        const maxLength = 50
        const truncate = hintedName.length > maxLength ? hintedName.slice(0,maxLength - 1) + "…" : hintedName;
        return {name: truncate, data: intervention.reduced_hload, fullName: hintedName};
    };

    const tryPatchTariffHint = (tariff: number[], index: number) => {
        const defaultLabel = {name: `Import Tariff #${index}`, data: tariff};
        if (hints === null) {
            return defaultLabel;
        }
        if (hints.tariffs === null || hints.tariffs.length < index) {
            console.error("Bundle Tariffs don't match SiteData tariffs!")
            return defaultLabel;
        }
        const productName = hints.tariffs[index].product_name;
        if (productName === "") {
            return defaultLabel;
        }
        const hintedName = snakeToDisplayName(productName);
        return {name: hintedName, data: tariff};
    }

    const tryPatchSolarHint = (solar: number[], index: number) => {
        const defaultLabel = {name: `Solar Yield #${index}`, data: solar};
        if (hints === null) {
            return defaultLabel;
        }
        if (hints.renewables === null || hints.renewables.length < index) {
            console.error("Bundle Renewables don't match SiteData solar!");
            return defaultLabel;
        }
        const solarName = hints.renewables[index].name;
        if (solarName === null || solarName === "") {
            return defaultLabel;
        }
        return {name: solarName, data: solar};
    }

    return (
        <Box sx={{marginTop: "2rem"}}>
            <DateRangeControls
                selectedStartDatetime={selectedStartDatetime}
                setSelectedStartDatetime={setSelectedStartDatetime}
                daysToKeep={daysToKeep}
                setDaysToKeep={setDaysToKeep}
                minDateTime={initialDatetime}
                maxDateTime={finalDatetime}
            />

            {usingAggregates && <Typography variant={"body1"} color={"info"}>Showing Daily Aggregates</Typography>}
            {!usingAggregates && <Typography variant={"body1"}>Showing Half-hourly Data</Typography>}

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
                        ...rangedSiteData.fabric_interventions
                            .map((intervention, index) => (tryPatchFabricHint(intervention, index)
                        ))
                    ]}
                    yLabel={"Energy (kWh)"}
                />

                <SiteDataLinePlot
                    title={"Solar Yields"}
                    xData={x_hh}
                    yData={rangedSiteData.solar_yields
                        .map((solar, index) => (tryPatchSolarHint(solar, index)))
                    }
                    yLabel={"Energy (kWh)"}
                />

                <SiteDataLinePlot
                    title={"Import Tariffs"}
                    xData={x_hh}
                    yData={rangedSiteData.import_tariffs
                        .map((tariff, index) => (tryPatchTariffHint(tariff, index)
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
                    yLabel={"gCO₂/kWh"}
                />
            </Grid>

            <TaskDataViewer
                data={siteData.baseline}
            />

            {hints && <HintViewer hints={hints}/>}

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
// @ts-ignore
const NoSiteDataToView = () => {

}

export const ErrorLoadingSiteData = () => (
    <Container maxWidth={"sm"} sx={{padding: "1em"}}>
        <Alert severity="error">Failed to load data for this site.</Alert>
    </Container>
)

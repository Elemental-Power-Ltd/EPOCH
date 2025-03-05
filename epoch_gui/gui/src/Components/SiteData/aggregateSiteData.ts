import {EpochSiteData} from "../../Models/Endpoints";
import dayjs from "dayjs";


/**
 * Aggregate the SiteData into daily values
 *
 * This code is not currently robust to edge cases with timestamps
 *
 * @param siteData
 */
export const aggregateSiteData = (siteData: EpochSiteData): EpochSiteData => {

    const start_time = dayjs(siteData.start_ts);
    const end_time = dayjs(siteData.end_ts);
    const length = siteData.building_eload.length;
    const secondsInADay = 24 * 60 * 60;

    const durationSeconds = end_time.unix() - start_time.unix();
    const timestepSeconds = durationSeconds / length;

    if (secondsInADay % timestepSeconds !== 0) {
        // timesteps do not evenly divide into 24h, we don't want to handle this right now
    }

    const timestepsInADay = secondsInADay / timestepSeconds;

    return {
        start_ts: siteData.start_ts,
        end_ts: siteData.end_ts,

        building_eload: aggregate(siteData.building_eload, timestepsInADay, "sum"),
        building_hload: aggregate(siteData.building_hload, timestepsInADay, "sum"),
        ev_eload: aggregate(siteData.ev_eload, timestepsInADay, "sum"),
        dhw_demand: aggregate(siteData.dhw_demand, timestepsInADay, "sum"),
        air_temperature: aggregate(siteData.air_temperature, timestepsInADay, "average"),
        grid_co2: aggregate(siteData.grid_co2, timestepsInADay, "average"),
        solar_yields: siteData.solar_yields.map((solar => aggregate(solar, timestepsInADay, "sum"))),
        import_tariffs: siteData.import_tariffs.map((tariff => aggregate(tariff, timestepsInADay, "average"))),
        fabric_interventions: siteData.fabric_interventions.map((intervention) => (
            {...intervention, reduced_hload: aggregate(intervention.reduced_hload, timestepsInADay, "sum")})),
        ashp_input_table: siteData.ashp_input_table,
        ashp_output_table: siteData.ashp_output_table

    }
}

const aggregate = (values: number[], chunkSize: number, mode: "sum" | "average"): number[] => {
    const result: number[] = [];

    for (let i = 0; i < values.length; i+= chunkSize) {
        const chunk = values.slice(i, i + chunkSize);

        const sum = chunk.reduce((acc, val) => acc + val, 0);
        if (mode === "sum") {
            result.push(sum)
        } else {
            result.push (sum / chunk.length)
        }
    }

    return result;
}

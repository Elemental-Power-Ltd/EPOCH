#include "SiteDataJson.hpp"

#include <chrono>
#include <nlohmann/json.hpp>

#include "FileHandling.hpp"
#include "../Simulation/SiteData.hpp"
#include "TaskDataJson.hpp"

using json = nlohmann::json;


void from_json(const json& j, FabricCostBreakdown& fcb) {
    fcb.name = j.at("name").get<std::string>();
    if (j.contains("area") && !j.at("area").is_null()) {
        fcb.area = j.at("area").get<float>();
    }
    else {
        fcb.area = std::nullopt;
    }
    fcb.cost = j.at("cost").get<float>();
}

void to_json(json& j, const FabricCostBreakdown& breakdown) {
    j = json{
        {"name", breakdown.name},
        {"cost", breakdown.cost}
    };
    if (breakdown.area.has_value()) {
        j["area"] = breakdown.area.value();
    }
    else {
        j["area"] = nullptr;
    }
}

void from_json(const json& j, FabricIntervention& intervention) {
    intervention.cost = j.at("cost").get<float>();
    if (j.contains("cost_breakdown") && !j.at("cost_breakdown").is_null()) {
        intervention.cost_breakdown = j.at("cost_breakdown").get<std::vector<FabricCostBreakdown>>();
    }
    else {
        intervention.cost_breakdown.clear();
    }
    intervention.reduced_hload = toEigen(j.at("reduced_hload").get<std::vector<float>>());
    intervention.peak_hload = j.value("peak_hload", 0.0f);  // default to 0.0f
}

void to_json(json& j, const FabricIntervention& intervention) {
    j = json{
        {"cost", intervention.cost},
        {"cost_breakdown", intervention.cost_breakdown},
        {"reduced_hload", toStdVec(intervention.reduced_hload)},
        {"peak_hload", intervention.peak_hload}
    };
}

// Utility to parse vector of vectors into a std::vector<year_TS>
static std::vector<year_TS> parseVectorOfVectors(const json& arr) {
    std::vector<year_TS> result;
    result.reserve(arr.size());
    for (const auto& subArr : arr) {
        auto tmp = subArr.get<std::vector<float>>();
        result.push_back(toEigen(tmp));
    }
    return result;
}

// Utility to convert back to a nested std::vec before deserialization
static std::vector<std::vector<float>> toVectorOfVectors(std::vector<year_TS> vec) {
    std::vector<std::vector<float>> output;
    output.reserve(vec.size());
    for (const auto& v : vec) {
        output.push_back(toStdVec(v));
    }
    return output;
}


namespace nlohmann {

    SiteData adl_serializer<SiteData>::from_json(const json& j) {
        std::string start_iso = j.at("start_ts").get<std::string>();
        std::string end_iso = j.at("end_ts").get<std::string>();

        auto start_ts = fromIso8601(start_iso);
        auto end_ts = fromIso8601(end_iso);

        // read in the site baseline
        TaskData baseline = j.at("baseline").get<TaskData>();

        // top-level vector fields
        year_TS building_eload = toEigen(j.at("building_eload").get<std::vector<float>>());

        year_TS building_hload = toEigen(j.at("building_hload").get<std::vector<float>>());
        float peak_hload = j.value("peak_hload", 0.0f);  // default to 0.0f
        year_TS dhw_demand = toEigen(j.at("dhw_demand").get<std::vector<float>>());
        year_TS air_temperature = toEigen(j.at("air_temperature").get<std::vector<float>>());
        year_TS grid_co2 = toEigen(j.at("grid_co2").get<std::vector<float>>());

        // optional entries
        auto reference_size = building_eload.size();
        year_TS ev_eload;
        if (j.contains("ev_eload")) {
            ev_eload = toEigen(j.at("ev_eload").get<std::vector<float>>());
        }
        else {
            ev_eload = year_TS::Zero(reference_size);
        }

        // Vectors of year_TS
        auto solar_yields = parseVectorOfVectors(j.at("solar_yields"));
        auto import_tariffs = parseVectorOfVectors(j.at("import_tariffs"));

        // Fabric interventions
        auto fabric_interventions = j.at("fabric_interventions").get<std::vector<FabricIntervention>>();

        // Heat pump tables
        auto ashp_in = j.at("ashp_input_table").get<std::vector<std::vector<float>>>();
        auto ashp_out = j.at("ashp_output_table").get<std::vector<std::vector<float>>>();

        Eigen::MatrixXf ashp_input_table = toEigen(ashp_in);
        Eigen::MatrixXf ashp_output_table = toEigen(ashp_out);

        return SiteData(
            start_ts,
            end_ts,
            std::move(baseline),
            std::move(building_eload),
            std::move(building_hload),
            peak_hload,
            std::move(ev_eload),
            std::move(dhw_demand),
            std::move(air_temperature),
            std::move(grid_co2),
            std::move(solar_yields),
            std::move(import_tariffs),
            std::move(fabric_interventions),
            std::move(ashp_input_table),
            std::move(ashp_output_table)
        );
    }

    void adl_serializer<SiteData>::to_json(json& j, const SiteData& sd) {
        // note that we don't write the derived values (timesteps and timestep_interval_s)
        j = json{
            {"start_ts", toIso8601(sd.start_ts)},
            {"end_ts", toIso8601(sd.end_ts)},
            {"baseline", sd.baseline},

            // Year_TS fields
            {"building_eload", toStdVec(sd.building_eload)},
            {"building_hload", toStdVec(sd.building_hload)},
            {"peak_hload", sd.peak_hload},
            {"ev_eload", toStdVec(sd.ev_eload)},
            {"dhw_demand", toStdVec(sd.dhw_demand)},
            {"air_temperature", toStdVec(sd.air_temperature)},
            {"grid_co2", toStdVec(sd.grid_co2)},

            // Vectors of year_TS
            {"solar_yields", toVectorOfVectors(sd.solar_yields)},
            {"import_tariffs", toVectorOfVectors(sd.import_tariffs)},

            // Fabric interventions
            {"fabric_interventions", sd.fabric_interventions},

            // Heat pump tables
            {"ashp_input_table", toStdVecOfVec(sd.ashp_input_table)},
            {"ashp_output_table", toStdVecOfVec(sd.ashp_output_table)}
        };
    }

} // namespace nlohmann
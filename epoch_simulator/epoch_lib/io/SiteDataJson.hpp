/* 
logic for serializing and deserializing SiteData to nlohmann json
*/
#pragma once

#include <nlohmann/json.hpp>

#include "../Simulation/SiteData.hpp"

void from_json(const nlohmann::json& j, FabricIntervention& intervention);
void to_json(nlohmann::json& j, const FabricIntervention& intervention);

namespace nlohmann {
    template <>
    struct adl_serializer<SiteData> {
        static SiteData from_json(const json& j);
        static void to_json(json& j, const SiteData& sd);
    };
}

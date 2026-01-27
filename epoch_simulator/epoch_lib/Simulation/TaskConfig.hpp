#pragma once

#include "Costs/CostData.hpp"

struct TaskConfig {
    bool use_boiler_upgrade_scheme = false;
    float general_grant_funding = 0.0f;
    int npv_time_horizon = 10;
    float npv_discount_factor = 0.0f;

    CapexModel capex_model = make_default_capex_prices();
    OpexModel opex_model = make_default_opex_prices();

    bool operator==(const TaskConfig&) const = default;
};

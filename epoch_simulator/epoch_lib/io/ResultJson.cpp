#include "ResultJson.hpp"
#include "EnumToString.hpp"


void to_json(json& j, const ScenarioComparison comparison) {
    j = json{
        {"meter_balance", comparison.meter_balance},
        {"operating_balance", comparison.operating_balance},
        {"cost_balance", comparison.cost_balance},
        {"npv_balance", comparison.npv_balance},
        {"payback_horizon_years", comparison.payback_horizon_years},
        {"return_on_investment", comparison.return_on_investment ? json(*comparison.return_on_investment) : json(nullptr)},
        {"carbon_balance_scope_1", comparison.carbon_balance_scope_1},
        {"carbon_balance_scope_2", comparison.carbon_balance_scope_2},
        {"combined_carbon_balance", comparison.combined_carbon_balance},
        {"carbon_cost", comparison.carbon_cost},
    };
}


void to_json(json& j, const SimulationMetrics m) {
    j = json{
        // energy totals in kWh
        {"total_gas_used", m.total_gas_used},
        {"total_electricity_imported", m.total_electricity_imported},
        {"total_electricity_generated", m.total_electricity_generated},
        {"total_electricity_exported", m.total_electricity_exported},
        {"total_electricity_curtailed", m.total_electricity_curtailed},
        {"total_electricity_used", m.total_electricity_used},

        {"total_heat_load", m.total_heat_load},
        {"total_dhw_load", m.total_dhw_load},
        {"total_ch_load", m.total_ch_load},

        {"total_electrical_shortfall", m.total_electrical_shortfall},
        {"total_heat_shortfall", m.total_heat_shortfall},
        {"total_ch_shortfall", m.total_ch_shortfall},
        {"total_dhw_shortfall", m.total_dhw_shortfall},
        {"peak_hload_shortfall", m.peak_hload_shortfall},

        // financial totals in £
        {"total_capex", m.total_capex},
        {"total_gas_import_cost", m.total_gas_import_cost},
        {"total_electricity_import_cost", m.total_electricity_import_cost},
        {"total_electricity_export_gain", m.total_electricity_export_gain},

        {"total_meter_cost", m.total_meter_cost},
        {"total_operating_cost", m.total_operating_cost},
        {"total_annualised_cost", m.total_annualised_cost},
        {"total_net_present_value", m.total_net_present_value},

        // carbon totals in kg CO2e
        {"total_scope_1_emissions", m.total_scope_1_emissions},
        {"total_scope_2_emissions", m.total_scope_2_emissions},
        {"total_combined_carbon_emissions", m.total_combined_carbon_emissions},

        // SAP
        {"environmental_impact_score",
            m.environmental_impact_score ? json(*m.environmental_impact_score) : json(nullptr)},
        {"environmental_impact_grade",
            m.environmental_impact_grade ? json(enumToString(*m.environmental_impact_grade)) : json(nullptr)},
    };
}

void to_json(json& j, const SimulationResult result) {
    j = json{
        {"comparison", result.comparison},
        {"metrics", result.metrics},
        {"baseline_metrics", result.baseline_metrics}
    };
}



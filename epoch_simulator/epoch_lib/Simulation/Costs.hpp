#pragma once
#include <limits> 
#include <Eigen/Core>

#include "TaskData.hpp"
#include "SiteData.hpp"
#include "../Definitions.hpp"
#include "Costs/Capex.hpp"
#include "Costs/Opex.hpp"

class Costs
{
public:

	Costs(const SiteData& siteData, const TaskData& taskData, const CapexBreakdown& capexBreakdown):
		mTaskData(taskData),
		mTimesteps(siteData.timesteps),
		mBaseline_elec_cost(0.0f),
		mBaseline_fuel_cost(0.0f),
		mBaselineImportTariff(siteData.import_tariffs[0]),
		mScenarioImportTariff(siteData.import_tariffs[taskData.grid ? taskData.grid->tariff_index : 0]),
		mScenario_import_cost(0.0f),
		mScenario_fuel_cost(0.0f),
		mScenario_export_cost(0.0f),
		mScenario_cost_balance(0.0f),
		mPayback_horizon_years(0.0f),
		mTotal_annualised_cost(0.0f),
		mBaseline_elec_CO2e(0.0f),
		mBaseline_fuel_CO2e(0.0f),
		mScenario_elec_CO2e(0.0f),
		mScenario_fuel_CO2e(0.0f),
		mScenario_export_CO2e(0.0f),
		mScenario_carbon_balance_scope_1(0.0f),
		mCapexBreakdown(capexBreakdown),
		// If there is no gas boiler we need to assume some defaults so use 90% efficiency and natural gas
		mBoiler_efficiency(taskData.gas_heater ? taskData.gas_heater->boiler_efficiency : 0.9f),
		mGasType(taskData.gas_heater ? taskData.gas_heater->gas_type : GasType::NATURAL_GAS)
	{	
	}

	
	void calculateCosts_no_CAPEX(const CostVectors& costVectors) {
		mOpexBreakdown = calculate_opex(mTaskData);

		calculate_total_annualised_cost();

		year_TS baseline_elec_load = costVectors.building_load_e;

		calculate_baseline_elec_cost(baseline_elec_load);

		year_TS baseline_heat_load = costVectors.heatload_h; // includes both baseline space heat and baseline DWH demand.


		float gasPrice = mGasType == GasType::NATURAL_GAS ? mMains_gas_price : mLPG_cost_price;
		year_TS import_gas_prices{ Eigen::VectorXf::Constant(mTimesteps, gasPrice) };

		calculate_baseline_fuel_cost(baseline_heat_load, import_gas_prices); 

		calculate_scenario_elec_cost(costVectors.grid_import_e);
		calculate_scenario_fuel_cost(costVectors.gas_import_h, import_gas_prices);
		calculate_scenario_export_cost(costVectors.grid_export_e, costVectors.grid_export_prices);

		calculate_scenario_EV_revenue(costVectors.actual_ev_load_e);
		calculate_scenario_HP_revenue(costVectors.actual_data_centre_load_e);
		calculate_scenario_LP_revenue(costVectors.actual_low_priority_load_e);

		calculate_scenario_cost_balance(mTotal_annualised_cost);

		calculate_payback_horizon();

		//========================================

		// Calculate time_dependent CO2e operational emissions section

		calculate_baseline_elec_CO2e(baseline_elec_load);

		calculate_baseline_gas_CO2e(baseline_heat_load);

		// trigger this function based on baseline fuel config, if it is LPG
		// calculate_baseline_LPG_CO2e(baseline_heat_load);

		calculate_scenario_elec_CO2e(costVectors.grid_import_e);

		calculate_scenario_gas_CO2e(costVectors.gas_import_h);

		calculate_scenario_export_CO2e(costVectors.grid_export_e);

		calculate_scenario_LP_CO2e(costVectors.actual_low_priority_load_e);

		calculate_scenario_carbon_balance_scope_1();

		calculate_scenario_carbon_balance_scope_2();
	}


	float calculate_ESS_annualised_cost() const {
		float ess_capex = mCapexBreakdown.ess_pcs_capex + mCapexBreakdown.ess_enclosure_capex + mCapexBreakdown.ess_enclosure_disposal;
		float ess_opex = mOpexBreakdown.ess_pcs_opex + mOpexBreakdown.ess_enclosure_opex;

		return (ess_capex / mESS_lifetime) + ess_opex;
	}

	float calculate_PV_annualised_cost() const {
		float pv_capex = mCapexBreakdown.pv_panel_capex + mCapexBreakdown.pv_roof_capex + mCapexBreakdown.pv_ground_capex + mCapexBreakdown.pv_BoP_capex;

		return (pv_capex / mPV_panel_lifetime) + mOpexBreakdown.pv_opex;
	}

	float calculate_EV_CP_annualised_cost() const {
		return (mCapexBreakdown.ev_charger_cost + mCapexBreakdown.ev_charger_install) / mEV_CP_lifetime;
	}

	float calculate_ASHP_annualised_cost() const {
		return mCapexBreakdown.heatpump_capex / mASHP_lifetime;
	}

	float calculate_DHW_annualised_cost ()	{
		return mCapexBreakdown.dhw_capex / mDHW_lifetime;
	}

	float calculate_Grid_annualised_cost() const {
		return mCapexBreakdown.grid_capex / mGrid_lifetime;
	}

	float calculate_Project_annualised_cost() const {

		float ESS_CAPEX = mCapexBreakdown.ess_pcs_capex + mCapexBreakdown.ess_enclosure_capex + mCapexBreakdown.ess_enclosure_disposal;
		float PV_CAPEX = mCapexBreakdown.pv_panel_capex + mCapexBreakdown.pv_roof_capex + mCapexBreakdown.pv_roof_capex + mCapexBreakdown.pv_BoP_capex;
		float EV_CP_CAPEX = mCapexBreakdown.ev_charger_cost + mCapexBreakdown.ev_charger_install;
		float ASHP_CAPEX = mCapexBreakdown.heatpump_capex;
		float DHW_CAPEX = mCapexBreakdown.dhw_capex;
		float Grid_CAPEX = mCapexBreakdown.grid_capex;

		float Project_cost = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX + DHW_CAPEX) * mProject_plan_develop_EPC;
		float Project_cost_grid = Grid_CAPEX * mProject_plan_develop_Grid;

		float Project_annualised_cost = (Project_cost + Project_cost_grid) / mProject_lifetime;

		return Project_annualised_cost;
	}

	// Calculate annualised costs

	void calculate_total_annualised_cost() {

		float ESS_annualised_cost = (
			(mCapexBreakdown.ess_pcs_capex + mCapexBreakdown.ess_enclosure_capex + mCapexBreakdown.ess_enclosure_disposal) 
			/ mESS_lifetime) + mOpexBreakdown.ess_pcs_opex + mOpexBreakdown.ess_enclosure_opex;
		
		float PV_annualised_cost = (
			(mCapexBreakdown.pv_panel_capex + mCapexBreakdown.pv_roof_capex + mCapexBreakdown.pv_ground_capex + mCapexBreakdown.pv_BoP_capex)
			/ mPV_panel_lifetime) + mOpexBreakdown.pv_opex;

		float EV_CP_annualised_cost = calculate_EV_CP_annualised_cost();

		float Grid_annualised_cost = calculate_Grid_annualised_cost();

		float ASHP_annualised_cost = calculate_ASHP_annualised_cost();

		float DHW_annualised_cost = calculate_DHW_annualised_cost();

		float Project_annualised_cost = calculate_Project_annualised_cost();

		mTotal_annualised_cost = Project_annualised_cost + ESS_annualised_cost + PV_annualised_cost + EV_CP_annualised_cost + Grid_annualised_cost + ASHP_annualised_cost + DHW_annualised_cost;
	}

	// time-dependent scenario costs

	void calculate_baseline_elec_cost(const year_TS& baseline_elec_load) {

		year_TS mBaseline_elec_cost_TS = (baseline_elec_load.array() * mBaselineImportTariff.array()); 
		mBaseline_elec_cost = mBaseline_elec_cost_TS.sum();
	};

	void calculate_baseline_fuel_cost(const year_TS& baseline_heat_load, const year_TS& import_fuel_prices) {
		float baseline_heat_load_sum = baseline_heat_load.sum();

		mBaseline_fuel_cost = (baseline_heat_load_sum * import_fuel_prices[0] / mBoiler_efficiency); 
	};

	void calculate_scenario_elec_cost(const year_TS& grid_import) {

		year_TS mScenario_import_cost_TS = (grid_import.array() * mScenarioImportTariff.array());
		mScenario_import_cost = mScenario_import_cost_TS.sum(); // just use fixed value for now
	};

	void calculate_scenario_fuel_cost(const year_TS& gas_import, const year_TS& import_fuel_prices) {
		float total_gas_import = gas_import.sum();

		// unlike the baseline, the scenario does not need to divide by the boiler efficiency
		// as the gas heater has already done this
		mScenario_fuel_cost = (total_gas_import * import_fuel_prices[0]);
	};

	void calculate_scenario_export_cost(const year_TS& grid_export, const year_TS& export_elec_prices) {
		
		// just use fixed value for now
		year_TS mScenario_export_cost_TS = (-grid_export.array() * (export_elec_prices.array()/100));
		mScenario_export_cost = mScenario_export_cost_TS.sum();
	};

	void calculate_scenario_EV_revenue(const year_TS& actual_ev_load) {
		year_TS mScenario_EV_revenueTS = actual_ev_load.array() * mEV_low_price; // will need to separate out EV charge tariffs later, assume all destination charging for now
		mScenario_EV_revenue = mScenario_EV_revenueTS.sum();
	};

	void calculate_scenario_HP_revenue(const year_TS& actual_data_centre_load) {
		year_TS mScenario_HP_revenueTS = actual_data_centre_load.array() * mHP_price;
		mScenario_HP_revenue = mScenario_HP_revenueTS.sum();
	};

	void calculate_scenario_LP_revenue(const year_TS& actual_low_priority_load) {
		mLP_price = mMains_gas_price/mBoiler_efficiency;
		year_TS mScenario_LP_revenueTS = actual_low_priority_load.array() * mLP_price; // will need to separate out EV charge tariffs later, assume all destination charging for now
		mScenario_LP_revenue = mScenario_LP_revenueTS.sum();
	}


	void calculate_scenario_cost_balance(float Total_annualised_cost) {
		mScenario_cost_balance = (mBaseline_elec_cost + mBaseline_fuel_cost) - (mScenario_import_cost + mScenario_fuel_cost + mScenario_export_cost - mScenario_EV_revenue - mScenario_HP_revenue - mScenario_LP_revenue + Total_annualised_cost);
	};

	/**
	* Calculate the payback hoizon of a scenario.
	* 
	* This is the capex divided by the yearly cost balance.
	* 
	* Note: we deliberately allow for negative payback horizons.
	* These should be considered invalid (as the scenario will never pay back)
	* but is useful to provide gradient information for optimisation.
	*/
	void calculate_payback_horizon() {
		if (mCapexBreakdown.total_capex <= 0) {
			// if we haven't spend any money then the payback horizon is 0
			mPayback_horizon_years = 0.0f;
		} else if (mScenario_cost_balance == 0.0f) {
			// return the smallest possible negative number
			mPayback_horizon_years = -1.0f / std::numeric_limits<float>::max();
		} else {
			mPayback_horizon_years = mCapexBreakdown.total_capex / mScenario_cost_balance;
		}
	};


	// Member functions to calculate CO2 equivalent operational emissions costs

	void calculate_baseline_elec_CO2e(const year_TS& baseline_elec_load) {
		float baseline_elec_load_sum = baseline_elec_load.sum();

		// just use fixed value for now
		mBaseline_elec_CO2e = (baseline_elec_load_sum * mSupplier_electricity_kg_CO2e); 
	};

	void calculate_baseline_gas_CO2e(const year_TS& baseline_heat_load) {
		float CO2e = mGasType == GasType::NATURAL_GAS ? mMains_gas_kg_C02e : mLPG_kg_C02e;

		float baseline_heat_load_sum = baseline_heat_load.sum();

		mBaseline_fuel_CO2e = (baseline_heat_load_sum * CO2e) / mBoiler_efficiency;
	};


	void calculate_scenario_elec_CO2e(const year_TS& grid_import) {
		float grid_import_sum = grid_import.sum();

		// just use fixed value for now
		mScenario_elec_CO2e = (grid_import_sum * mSupplier_electricity_kg_CO2e);
	};

	void calculate_scenario_gas_CO2e(const year_TS& total_heat_shortfall) {
		float CO2e = mGasType == GasType::NATURAL_GAS ? mMains_gas_kg_C02e : mLPG_kg_C02e;

		float total_heat_shortfall_sum = total_heat_shortfall.sum();

		// unlike the baseline, the scenario does not need to divide by the boiler efficiency
		// as the gas heater has already done this
		mScenario_fuel_CO2e = (total_heat_shortfall_sum * CO2e);
	};


	void calculate_scenario_export_CO2e(const year_TS& grid_export) {
		float grid_export_sum = grid_export.sum();

		mScenario_export_CO2e = (-grid_export_sum * mSupplier_electricity_kg_CO2e);
	};

	void calculate_scenario_LP_CO2e(const year_TS& actual_low_priority_load) {
	
		year_TS mScenario_LP_CO2eTS = actual_low_priority_load.array() * mMains_gas_kg_C02e; // assume the counterfactual of LP heat is gas based heat emissions
		mScenario_LP_CO2e =  -mScenario_LP_CO2eTS.sum();
	}


	void calculate_scenario_carbon_balance_scope_1() {
		mScenario_carbon_balance_scope_1 = (mBaseline_fuel_CO2e) - (mScenario_fuel_CO2e + mScenario_LP_CO2e); /// mScenario_LP_CO2e is the CO2 saved by not heating LP load via burning gas, so subtract a negative
	};

	void calculate_scenario_carbon_balance_scope_2() {
		mScenario_carbon_balance_scope_2 = (mBaseline_elec_CO2e) - (mScenario_elec_CO2e + mScenario_export_CO2e);
	};

	float get_project_CAPEX() const {
		return mCapexBreakdown.total_capex;
	}

	float get_scenario_cost_balance() const {
		return mScenario_cost_balance;
	}

	float get_payback_horizon_years() const {
		return mPayback_horizon_years;
	}

	float get_scenario_carbon_balance_scope_1() const {
		return mScenario_carbon_balance_scope_1;
	}

	float get_scenario_carbon_balance_scope_2() const {
		return mScenario_carbon_balance_scope_2;
	}

	float get_total_annualised_cost() const {
		return mTotal_annualised_cost;
	}

	float get_scenario_fuel_cost() const {
		return mScenario_fuel_cost;
	}

	float get_scenario_import_cost() const {
		return mScenario_import_cost;
	}

	float get_scenario_export_gains() const {
		// we store the export as a negative cost, multiply by -1 to get the gain
		return -1.0f * mScenario_export_cost;
	}

	// "hard wired" constants for the moment
	private:
		const TaskData& mTaskData;
		const size_t mTimesteps;

		// coefficient applied to local infrastructure CAPEX (decimal, not percentage)
		const float mProject_plan_develop_EPC = 0.0f;  // set to zero for the moment as design and PM included in kit installation costs
		// coefficient applied to grid infrastructure CAPEX (decimal, not percentage)
		const float mProject_plan_develop_Grid = 0.1f; 

		const float mMains_gas_kg_C02e = 0.201f; // kg/kWh(w2h) 
		const float mLPG_kg_C02e = 0.239f; // kg/kWh (well2heat)
		// every kWh that goes into an EV saves this much on the counterfactual of an ICE petrol vehicle
		const float mPetrol_displace_kg_CO2e = 0.9027f;

		// coefficient applied to convert gas kWh to heat kWh (decimal, not percentage)
		const float mBoiler_efficiency;
		const GasType mGasType;

		const float mMains_gas_price = 0.068f; // £/kWh  
		const float mLPG_cost_price = 0.122f; // £/kWh

		const float mSupplier_electricity_kg_CO2e = 0.182f; //

		year_TS mBaselineImportTariff;
		year_TS mScenarioImportTariff;

		// site price

		float mEV_low_price = 0.45f; // £/kWh site price for destination EV charging, 22 kW and below
		float mEV_high_price = 0.79f; //£/kWh site price for high power EV charging, 50 KW and above
		float mHP_price = 0.50f; // £/kWh site price for data centre compute (hi priority load)
		float mLP_price ; // assume this is just the equivalent lowest cost fossil fuel derived heat


		// plant lifetimes in years

		const float mESS_lifetime = 15.0f;
		const float mPV_panel_lifetime = 25.0f;
		const float mEV_CP_lifetime = 15.0f;
		const float mGrid_lifetime = 25.0f;
		const float mASHP_lifetime = 10.0f;
		const float mDHW_lifetime = 12.0f;
		const float mProject_lifetime = 10.0f;

		// Grid prices are currently part of the config

		float mBaseline_elec_cost;
		float mBaseline_fuel_cost;

		
		float mScenario_import_cost;
		float mScenario_fuel_cost;
		float mScenario_export_cost;
		float mScenario_cost_balance;
		CapexBreakdown mCapexBreakdown;
		OpexBreakdown mOpexBreakdown;
		float mPayback_horizon_years;
		float mTotal_annualised_cost;

		// variables for calculating CO2e operational emissions
		float mBaseline_elec_CO2e;
		float mBaseline_fuel_CO2e;

		float mScenario_elec_CO2e;
		float mScenario_fuel_CO2e;
		float mScenario_export_CO2e;

		float mScenario_LP_CO2e;

		float mScenario_carbon_balance_scope_1;

		float mScenario_carbon_balance_scope_2;

		float mScenario_EV_revenue;

		float mScenario_HP_revenue;

		float mScenario_LP_revenue;

};


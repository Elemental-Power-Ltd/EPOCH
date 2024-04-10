#pragma once

#include <Eigen/Core>

#include "Config.h"
#include "../Definitions.h"
#include "Eload.h"
#include "Hload.h"
#include "Grid.h"

class Costs
{
public:

	Costs(const Config& config):
		mConfig(config),
		mBaseline_elec_cost(0.0f),
		mBaseline_fuel_cost(0.0f),
		mScenario_import_cost(0.0f),
		mScenario_fuel_cost(0.0f),
		mScenario_export_cost(0.0f),
		mScenario_cost_balance(0.0f),
		mProject_CAPEX(0.0f),
		mPayback_horizon_years(0.0f),
		mTotal_annualised_cost(0.0f),
		mBaseline_elec_CO2e(0.0f),
		mBaseline_fuel_CO2e(0.0f),
		mScenario_elec_CO2e(0.0f),
		mScenario_fuel_CO2e(0.0f),
		mScenario_export_CO2e(0.0f),
		mScenario_carbon_balance(0.0f)
	{}

	void calculateCosts(const Eload& eload, const Hload& hload, const Grid& grid) {

		float ESS_kW = std::max(mConfig.ESS_charge_power, mConfig.ESS_discharge_power);
		float PV_kWp_total = mConfig.ScalarRG1 + mConfig.ScalarRG2 + mConfig.ScalarRG3 + mConfig.ScalarRG4;

		// need to add a new config parameter here
		const float IMPORT_FUEL_PRICE = 12.2f;
		const float BOILER_EFFICIENCY = 0.9f;

		const int s7_EV_CP_number = 0;
		const int f22_EV_CP_number = 3;
		const int r50_EV_CP_number = 0;
		const int u150_EV_CP_number = 0;
		const float kw_grid_upgrade = 0; 
		const float heatpump_electrical_capacity = 70.0;

		calculate_total_annualised_cost(ESS_kW, mConfig.ESS_capacity, PV_kWp_total, s7_EV_CP_number,
			f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number, kw_grid_upgrade, heatpump_electrical_capacity);

		// for now, simply fix import/export price
		year_TS import_elec_prices{ Eigen::VectorXf::Constant(mConfig.calculate_timesteps(), mConfig.Import_kWh_price) };
		year_TS export_elec_prices{ Eigen::VectorXf::Constant(mConfig.calculate_timesteps(), mConfig.Export_kWh_price) };
		year_TS baseline_elec_load = eload.getTotalFixLoad() + grid.getActualHighPriorityLoad();

		calculate_baseline_elec_cost(baseline_elec_load, import_elec_prices);

		year_TS baseline_heat_load = hload.getHeatload() + grid.getActualLowPriorityLoad();
		year_TS import_fuel_prices{ Eigen::VectorXf::Constant(mConfig.calculate_timesteps(), IMPORT_FUEL_PRICE) };

		calculate_baseline_fuel_cost(baseline_heat_load, import_fuel_prices, BOILER_EFFICIENCY);
		calculate_scenario_elec_cost(grid.getGridImport(), import_elec_prices);
		calculate_scenario_fuel_cost(hload.getHeatShortfall(), import_fuel_prices);
		calculate_scenario_export_cost(grid.getGridExport(), export_elec_prices);

		calculate_scenario_cost_balance(mTotal_annualised_cost);

		//========================================

		calculate_Project_CAPEX(ESS_kW, mConfig.ESS_capacity, PV_kWp_total, s7_EV_CP_number,
			f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number, kw_grid_upgrade, heatpump_electrical_capacity);

		//========================================

		calculate_payback_horizon();

		//========================================

		// Calculate time_dependent CO2e operational emissions section

		calculate_baseline_elec_CO2e(baseline_elec_load);

		calculate_baseline_fuel_CO2e(baseline_heat_load);

		calculate_scenario_elec_CO2e(grid.getGridImport());

		calculate_scenario_fuel_CO2e(hload.getHeatShortfall());

		calculate_scenario_export_CO2e(grid.getGridExport());

		calculate_scenario_carbon_balance();
	}
	
	//ESS COSTS

	// these functions account for headroom built in to Grid_connection to take import/export power peaks intratimestep
	float calculate_ESS_PCS_CAPEX(float ESS_kW) const {
		// thresholds in kW units
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW
		float small_cost = 250.0;
		float mid_cost = 125.0;
		float large_cost = 75.0;

		float ESS_PCS_CAPEX = 0;

		if (ESS_kW < small_thresh) {
			ESS_PCS_CAPEX = small_cost * ESS_kW;
		} else if (small_thresh < ESS_kW && ESS_kW < mid_thresh) {
			ESS_PCS_CAPEX = (small_cost * small_thresh) + ((ESS_kW - small_thresh) * mid_cost);
		} else if (ESS_kW > mid_thresh) {
			ESS_PCS_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kW - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_PCS_CAPEX;
	}

	float calculate_ESS_PCS_OPEX(float ESS_kW) const {
		// threholds in kW units
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW
		float small_cost = 8.0;
		float mid_cost = 4.0;
		float large_cost = 1.0;

		float ESS_PCS_OPEX = 0;

		if (ESS_kW < small_thresh) {
			ESS_PCS_OPEX = small_cost * ESS_kW;
		} else if (small_thresh < ESS_kW && ESS_kW < mid_thresh) {
			ESS_PCS_OPEX = (small_cost * small_thresh) + ((ESS_kW - small_thresh) * mid_cost);
		} else if (ESS_kW > mid_thresh) {
			ESS_PCS_OPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kW - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_PCS_OPEX;
	}

	float calculate_ESS_ENCLOSURE_CAPEX(float ESS_kWh) const {
		// threholds in kW units
		float small_thresh = 100;
		float mid_thresh = 2000;

		// costs in £ / kWh
		float small_cost = 480.0;
		float mid_cost = 360.0;
		float large_cost = 300.0;

		float ESS_ENCLOSURE_CAPEX = 0;

		if (ESS_kWh < small_thresh) {
			ESS_ENCLOSURE_CAPEX = small_cost * ESS_kWh;
		} else if (small_thresh < ESS_kWh && ESS_kWh < mid_thresh) {
			ESS_ENCLOSURE_CAPEX = (small_cost * small_thresh) + ((ESS_kWh - small_thresh) * mid_cost);
		} else if (ESS_kWh > mid_thresh) {
			ESS_ENCLOSURE_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kWh - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_ENCLOSURE_CAPEX;
	}

	float calculate_ESS_ENCLOSURE_OPEX(float ESS_kWh) const {
		// threholds in kWh units
		float small_thresh = 100;
		float mid_thresh = 2000;

		// costs in £ / kWh
		float small_cost = 10.0;
		float mid_cost = 4.0;
		float large_cost = 2.0;

		float ESS_ENCLOSURE_OPEX = 0;

		if (ESS_kWh < small_thresh) {
			ESS_ENCLOSURE_OPEX = small_cost * ESS_kWh;
		} else if (small_thresh < ESS_kWh && ESS_kWh < mid_thresh) {
			ESS_ENCLOSURE_OPEX = (small_cost * small_thresh) + ((ESS_kWh - small_thresh) * mid_cost);
		} else if (ESS_kWh > mid_thresh) {
			ESS_ENCLOSURE_OPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kWh - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_ENCLOSURE_OPEX;
	}

	// thresholds in kWh units
	float calculate_ESS_ENCLOSURE_DISPOSAL(float ESS_kWh) const {
		float small_thresh = 100;
		float mid_thresh = 2000;

		// costs in £ / kWh
		float small_cost = 30.0;
		float mid_cost = 20.0;
		float large_cost = 15.0;

		float ESS_ENCLOSURE_DISPOSAL = 0;

		if (ESS_kWh < small_thresh) {
			ESS_ENCLOSURE_DISPOSAL = small_cost * ESS_kWh;
		} else if (small_thresh < ESS_kWh && ESS_kWh < mid_thresh) {
			ESS_ENCLOSURE_DISPOSAL = (small_cost * small_thresh) + ((ESS_kWh - small_thresh) * mid_cost);
		} else if (ESS_kWh > mid_thresh) {
			ESS_ENCLOSURE_DISPOSAL = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((ESS_kWh - small_thresh - mid_thresh) * large_cost);
		}

		return ESS_ENCLOSURE_DISPOSAL;
	}

	//PHOTOVOLTAIC COSTS (All units of kWp are DC)

	float calculate_PVpanel_CAPEX(float PV_kWp_total) const {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW DC
		float small_cost = 150.0;
		float mid_cost = 110.0;
		float large_cost = 95.0;

		float PVpanel_CAPEX = 0;

		if (PV_kWp_total < small_thresh) {
			PVpanel_CAPEX = small_cost * PV_kWp_total;
		} else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh) {
			PVpanel_CAPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		} else if (PV_kWp_total > mid_thresh) {
			PVpanel_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PVpanel_CAPEX;
	}

	float calculate_PVBoP_CAPEX(float PV_kWp_total) const {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 120.0;
		float mid_cost = 88.0;
		float large_cost = 76.0;

		float PVBoP_CAPEX = 0;

		if (PV_kWp_total < small_thresh) {
			PVBoP_CAPEX = small_cost * PV_kWp_total;
		} else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh) {
			PVBoP_CAPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		} else if (PV_kWp_total > mid_thresh) {
			PVBoP_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PVBoP_CAPEX;
	}

	float calculate_PVroof_CAPEX(float PV_kWp_total) const {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 250.0;
		float mid_cost = 200.0;
		float large_cost = 150.0;

		float PVroof_CAPEX = 0;

		if (PV_kWp_total < small_thresh) {
			PVroof_CAPEX = small_cost * PV_kWp_total;
		} else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh) {
			PVroof_CAPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		} else if (PV_kWp_total > mid_thresh) {
			PVroof_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PVroof_CAPEX;
	}

	float calculate_PVground_CAPEX(float PV_kWp_total) const {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 150.0;
		float mid_cost = 125.0;
		float large_cost = 100.0;

		float PVground_CAPEX = 0;

		if (PV_kWp_total < small_thresh) {
			PVground_CAPEX = small_cost * PV_kWp_total;
		} else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh) {
			PVground_CAPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		} else if (PV_kWp_total > mid_thresh) {
			PVground_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PVground_CAPEX;
	}

	float calculate_PV_OPEX(float PV_kWp_total) const {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 2.0;
		float mid_cost = 1.0;
		float large_cost = 0.50;

		float PV_OPEX = 0;

		if (PV_kWp_total < small_thresh) {
			PV_OPEX = small_cost * PV_kWp_total;
		} else if (small_thresh < PV_kWp_total && PV_kWp_total < mid_thresh) {
			PV_OPEX = (small_cost * small_thresh) + ((PV_kWp_total - small_thresh) * mid_cost);
		} else if (PV_kWp_total > mid_thresh) {
			PV_OPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((PV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return PV_OPEX;
	}

	// EV charge point costs 

	// Cost model for EV charge points is based on per unit of each charger type, 7 kW, 22 kW, 50 kW and 150 kW

	float calculate_EV_CP_cost(int s7_EV_CP_number, 
		int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number) const {
		// costs in £ / unit (1 hd unit 2 connectors)
		float s7_EV_cost = 1200.00;
		float f22_EV_cost = 2500.00;
		float r50_EV_cost = 20000.00;
		float u150_EV_cost = 60000.00;

		float EV_CP_COST = (float(s7_EV_CP_number) * s7_EV_cost) + (float(f22_EV_CP_number) * f22_EV_cost) 
			+ (float(r50_EV_CP_number) * r50_EV_cost) + (float(u150_EV_CP_number) * u150_EV_cost);

		return EV_CP_COST;
	}

	float calculate_EV_CP_install(int s7_EV_CP_number,
		int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number) const {
		// costs in £ / unit (1 hd unit 2 connectors)
		float s7_EV_install = 600.00;
		float f22_EV_install = 1000.00;
		float r50_EV_install = 3000.00;
		float u150_EV_install = 10000.00;

		float EV_CP_INSTALL = (float(s7_EV_CP_number) * s7_EV_install) + (float(f22_EV_CP_number) * f22_EV_install)
			+ (float(r50_EV_CP_number) * r50_EV_install) + (float(u150_EV_CP_number) * u150_EV_install);

		return EV_CP_INSTALL;
	}

	// Grid upgrade costs

	float calculate_Grid_CAPEX(float kW_max) const {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW DC
		float small_cost = 240.0;
		float mid_cost = 160.0;
		float large_cost = 120.0;

		float Grid_CAPEX = 0;

		if (kW_max < small_thresh) {
			Grid_CAPEX = small_cost * kW_max;
		} else if (small_thresh < kW_max && kW_max < mid_thresh) {
			Grid_CAPEX = (small_cost * small_thresh) + ((kW_max - small_thresh) * mid_cost);
		} else if (kW_max > mid_thresh) {
			Grid_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((kW_max - small_thresh - mid_thresh) * large_cost);
		}

		return Grid_CAPEX;
	}

	// ASHP CAPEX costs

	float calculate_ASHP_CAPEX(float heatpump_electrical_capacity) const {
		float small_thresh = 10;
		float mid_thresh = 100;

		// costs in £ / kW DC
		float small_cost = 1000.0;
		float mid_cost = 1000.0;
		float large_cost = 1000.0;

		float ASHP_CAPEX = 0;

		if (heatpump_electrical_capacity < small_thresh) {
			ASHP_CAPEX = small_cost * heatpump_electrical_capacity;
		} else if (small_thresh < heatpump_electrical_capacity && heatpump_electrical_capacity < mid_thresh) {
			ASHP_CAPEX = (small_cost * small_thresh) + ((heatpump_electrical_capacity - small_thresh) * mid_cost);
		} else if (heatpump_electrical_capacity > mid_thresh) {
			ASHP_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((heatpump_electrical_capacity - small_thresh - mid_thresh) * large_cost);
		}

		return ASHP_CAPEX;
	}

	float calculate_ESS_annualised_cost(float ESS_kW, float ESS_kWh, float PV_kWp_total) const {
		float ESS_annualised_cost = ((calculate_ESS_PCS_CAPEX(ESS_kW) + calculate_ESS_ENCLOSURE_CAPEX(ESS_kWh) + calculate_ESS_ENCLOSURE_DISPOSAL(ESS_kWh)) / mESS_lifetime) + calculate_ESS_PCS_OPEX(ESS_kW) + calculate_ESS_ENCLOSURE_OPEX(ESS_kWh);
		return ESS_annualised_cost;
	}

	float calculate_PV_annualised_cost(float PV_kWp_total) const {
		float PV_annualised_cost = ((calculate_PVpanel_CAPEX(PV_kWp_total) + calculate_PVBoP_CAPEX(PV_kWp_total) + calculate_PVroof_CAPEX(0) + calculate_PVground_CAPEX(PV_kWp_total)) / mPV_panel_lifetime) + calculate_PV_OPEX(PV_kWp_total);
		return PV_annualised_cost;
	}

	float calculate_EV_CP_annualised_cost(int s7_EV_CP_number, 
		int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number) const {
		float EV_CP_annualised_cost = 
			(
			calculate_EV_CP_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number) + 
			calculate_EV_CP_install(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number)
			) / mEV_CP_lifetime;

		return EV_CP_annualised_cost;
	}

	float calculate_ASHP_annualised_cost(float heatpump_electrical_capacity) const {
		float ASHP_annualised_cost = calculate_ASHP_CAPEX(heatpump_electrical_capacity) / mASHP_lifetime;
		return ASHP_annualised_cost;
	}

	float calculate_Grid_annualised_cost(float kw_grid_upgrade) const {
		float Grid_annualised_cost = calculate_Grid_CAPEX(kw_grid_upgrade) / mGrid_lifetime;
		return Grid_annualised_cost;
	}

	float calculate_Project_annualised_cost(float ESS_kW, float ESS_kWh, float PV_kWp_total, int s7_EV_CP_number, 
		int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number, float kw_grid_upgrade, float heatpump_electrical_capacity) const {

		float ESS_CAPEX = calculate_ESS_PCS_CAPEX(ESS_kW) + calculate_ESS_ENCLOSURE_CAPEX(ESS_kWh) + calculate_ESS_ENCLOSURE_DISPOSAL(ESS_kWh);
		float PV_CAPEX = calculate_PVpanel_CAPEX(PV_kWp_total) + calculate_PVBoP_CAPEX(PV_kWp_total) + calculate_PVroof_CAPEX(0) + calculate_PVground_CAPEX(PV_kWp_total);
		float EV_CP_CAPEX = calculate_EV_CP_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number) + calculate_EV_CP_install(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number);
		float ASHP_CAPEX = calculate_ASHP_CAPEX(heatpump_electrical_capacity);
		float Grid_CAPEX = calculate_Grid_CAPEX(kw_grid_upgrade);

		float Project_cost = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX) * mProject_plan_develop_EPC;
		float Project_cost_grid = Grid_CAPEX * mProject_plan_develop_Grid;

		float Project_annualised_cost = (Project_cost + Project_cost_grid) / mProject_lifetime;

		return Project_annualised_cost;
	}

	void calculate_Project_CAPEX(float ESS_kW, float ESS_kWh, float PV_kWp_total, int s7_EV_CP_number, 
		int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number, float kw_grid_upgrade, float heatpump_electrical_capacity) {

		float ESS_CAPEX = calculate_ESS_PCS_CAPEX(ESS_kW) + calculate_ESS_ENCLOSURE_CAPEX(ESS_kWh) + calculate_ESS_ENCLOSURE_DISPOSAL(ESS_kWh);
		float PV_CAPEX = calculate_PVpanel_CAPEX(PV_kWp_total) + calculate_PVBoP_CAPEX(PV_kWp_total) + calculate_PVroof_CAPEX(0) + calculate_PVground_CAPEX(PV_kWp_total);
		float EV_CP_CAPEX = calculate_EV_CP_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number) + calculate_EV_CP_install(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number);
		float ASHP_CAPEX = calculate_ASHP_CAPEX(heatpump_electrical_capacity);
		float Grid_CAPEX = calculate_Grid_CAPEX(kw_grid_upgrade);

		float Project_cost = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX) * mProject_plan_develop_EPC;
		float Project_cost_grid = Grid_CAPEX * mProject_plan_develop_Grid;

		mProject_CAPEX = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX + Project_cost + Project_cost_grid);
	}

	// Calculate annualised costs

	void calculate_total_annualised_cost(float ESS_kW, float ESS_kWh, float PV_kWp_total, int s7_EV_CP_number, 
		int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number, float kw_grid_upgrade, float heatpump_electrical_capacity) {

		float ESS_annualised_cost = ((calculate_ESS_PCS_CAPEX(ESS_kW) + calculate_ESS_ENCLOSURE_CAPEX(ESS_kWh) + calculate_ESS_ENCLOSURE_DISPOSAL(ESS_kWh)) / mESS_lifetime) + calculate_ESS_PCS_OPEX(ESS_kW) + calculate_ESS_ENCLOSURE_OPEX(ESS_kWh);
		
		float PV_annualised_cost = ((calculate_PVpanel_CAPEX(PV_kWp_total) + calculate_PVBoP_CAPEX(PV_kWp_total) + calculate_PVroof_CAPEX(0) + calculate_PVground_CAPEX(PV_kWp_total)) / mPV_panel_lifetime) + calculate_PV_OPEX(PV_kWp_total);

		float EV_CP_annualised_cost = calculate_EV_CP_annualised_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number);

		float Grid_annualised_cost = calculate_Grid_annualised_cost(kw_grid_upgrade);

		float ASHP_annualised_cost = calculate_ASHP_annualised_cost(heatpump_electrical_capacity);

		float Project_annualised_cost = calculate_Project_annualised_cost(ESS_kW, ESS_kWh, PV_kWp_total, s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number, kw_grid_upgrade, heatpump_electrical_capacity);

		mTotal_annualised_cost = Project_annualised_cost + ESS_annualised_cost + PV_annualised_cost + EV_CP_annualised_cost + Grid_annualised_cost + ASHP_annualised_cost;
	}

	// time-dependent scenario costs

	void calculate_baseline_elec_cost(const year_TS& baseline_elec_load, const year_TS& import_elec_prices) {
		float baseline_elec_load_sum = baseline_elec_load.sum();

		mBaseline_elec_cost = (baseline_elec_load_sum * import_elec_prices[0]) / 100; // just use fixed value for now
	};

	void calculate_baseline_fuel_cost(const year_TS& baseline_heat_load, const year_TS& import_fuel_prices, float boiler_efficiency) {
		float baseline_heat_load_sum = baseline_heat_load.sum();

		mBaseline_fuel_cost = (baseline_heat_load_sum * import_fuel_prices[0] / boiler_efficiency) / 100; // this should be changed to divided by boiler efficiency
	};

	void calculate_scenario_elec_cost(const year_TS& grid_import, const year_TS& import_elec_prices) {
		float grid_import_sum = grid_import.sum();

		mScenario_import_cost = (grid_import_sum * import_elec_prices[0]) / 100; // just use fixed value for now
	};

	void calculate_scenario_fuel_cost(const year_TS& total_heat_shortfall, const year_TS& import_fuel_prices) {
		float total_heat_shortfall_sum = total_heat_shortfall.sum();

		mScenario_fuel_cost = (total_heat_shortfall_sum * import_fuel_prices[0] / mBoiler_efficiency) / 100; // this should be changed to divided by boiler efficiency
	};

	void calculate_scenario_export_cost(const year_TS& grid_export, const year_TS& export_elec_prices) {
		float grid_export_sum = grid_export.sum();

		// just use fixed value for now
		mScenario_export_cost = (-grid_export_sum * export_elec_prices[0]) / 100;
	};

	void calculate_scenario_cost_balance(float Total_annualised_cost) {
		mScenario_cost_balance = (mBaseline_elec_cost + mBaseline_fuel_cost) - (mScenario_import_cost + mScenario_fuel_cost + mScenario_export_cost + Total_annualised_cost);
	};

	void calculate_payback_horizon() {
		mPayback_horizon_years = mProject_CAPEX / mScenario_cost_balance;
	};


	// Member functions to calculate CO2 equivalent operational emissions costs

	void calculate_baseline_elec_CO2e(const year_TS& baseline_elec_load) {
		float baseline_elec_load_sum = baseline_elec_load.sum();

		// just use fixed value for now
		mBaseline_elec_CO2e = (baseline_elec_load_sum * mSupplier_electricity_kg_CO2e); 
	};

	void calculate_baseline_fuel_CO2e(const year_TS& baseline_heat_load) {
		float baseline_heat_load_sum = baseline_heat_load.sum();

		// this should be changed to divided by boiler efficiency
		mBaseline_fuel_CO2e = (baseline_heat_load_sum * mLPG_kg_C02e / mBoiler_efficiency); 
	};

	void calculate_scenario_elec_CO2e(const year_TS& grid_import) {
		float grid_import_sum = grid_import.sum();

		// just use fixed value for now
		mScenario_elec_CO2e = (grid_import_sum * mSupplier_electricity_kg_CO2e);
	};

	void calculate_scenario_fuel_CO2e(const year_TS& total_heat_shortfall) {
		float total_heat_shortfall_sum = total_heat_shortfall.sum();

		mScenario_fuel_CO2e = (total_heat_shortfall_sum * mLPG_kg_C02e / mBoiler_efficiency);
	};

	void calculate_scenario_export_CO2e(const year_TS& grid_export) {
		float grid_export_sum = grid_export.sum();

		mScenario_export_CO2e = (-grid_export_sum * mSupplier_electricity_kg_CO2e);
	};

	void calculate_scenario_carbon_balance() {
		mScenario_carbon_balance = (mBaseline_elec_CO2e + mBaseline_fuel_CO2e) - (mScenario_elec_CO2e + mScenario_fuel_CO2e + mScenario_export_CO2e);
	};

	float get_project_CAPEX() const {
		return mProject_CAPEX;
	}

	float get_scenario_cost_balance() const {
		return mScenario_cost_balance;
	}

	float get_payback_horizon_years() const {
		return mPayback_horizon_years;
	}

	float get_scenario_carbon_balance() const {
		return mScenario_carbon_balance;
	}

	float get_total_annualised_cost() const {
		return mTotal_annualised_cost;
	}

	// "hard wired" constants for the moment
	private:
		const Config& mConfig;

		// coefficient applied to local infrastructure CAPEX (decimal, not percentage)
		const float mProject_plan_develop_EPC = 0.1f; 
		// coefficient applied to grid infrastructure CAPEX (decimal, not percentage)
		const float mProject_plan_develop_Grid = 0.1f; 

		const float mMains_gas_kg_C02e = 0.201f; // kg/kWh(w2h) 
		const float mLPG_kg_C02e = 0.239f; // kg/kWh (well2heat)
		// every kWh that goes into an EV saves this much on the counterfactual of an ICE petrol vehicle
		const float mPetrol_displace_kg_CO2e = 0.9037f;

		// coefficient applied to convert gas kWh to heat kWh (decimal, not percentage)
		const float mBoiler_efficiency = 0.9f; 
		const float mMains_gas_price = 0.068f; // £/kWh  
		const float mLPG_cost_price = 0.122f; // £/kWh

		const float mSupplier_electricity_kg_CO2e = 0.182f; //

		// plant lifetimes in years

		const float mESS_lifetime = 15.0f;
		const float mPV_panel_lifetime = 25.0f;
		const float mEV_CP_lifetime = 15.0f;
		const float mGrid_lifetime = 25.0f;
		const float mASHP_lifetime = 10.0f;
		const float mProject_lifetime = 10.0f;

		// Grid prices are currently part of the config

		float mBaseline_elec_cost;
		float mBaseline_fuel_cost;
		float mScenario_import_cost;
		float mScenario_fuel_cost;
		float mScenario_export_cost;
		float mScenario_cost_balance;
		float mProject_CAPEX;
		float mPayback_horizon_years;
		float mTotal_annualised_cost;

		// variables for calculating CO2e operational emissions
		float mBaseline_elec_CO2e;
		float mBaseline_fuel_CO2e;
		float mScenario_elec_CO2e;
		float mScenario_fuel_CO2e;
		float mScenario_export_CO2e;

		float mScenario_carbon_balance;
};


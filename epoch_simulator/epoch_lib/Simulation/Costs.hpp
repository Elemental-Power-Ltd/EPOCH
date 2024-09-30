#pragma once
#include <limits> 
#include <Eigen/Core>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class Costs
{
public:

	Costs(const HistoricalData& historicalData, const TaskData& taskData):
		mTaskData(taskData),
		mBaseline_elec_cost(0.0f),
		mBaseline_fuel_cost(0.0f),
		mImport_prices(historicalData.importtariff_data),
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
	{
		mESS_kW = std::max(mTaskData.ESS_charge_power, mTaskData.ESS_discharge_power);
		mESS_kWmin = std::min(mTaskData.ESS_charge_power, mTaskData.ESS_discharge_power);
		mESS_kWh = mTaskData.ESS_capacity;
		mPV_kWp_total = mTaskData.ScalarRG1 + mTaskData.ScalarRG2 + mTaskData.ScalarRG3 + mTaskData.ScalarRG4;
		
		// the following will need connecting to new task data input

		mPV_kWp_ground = mPV_kWp_total; // need to add types of PV to taskdata to allocated costs.
		mPV_kWp_roof = 0;
		mkW_Grid = 0; // set Grid upgrade to zero for the moment
	
	}

	void calculate_Project_CAPEX() {

		calculate_ESS_PCS_CAPEX();
		calculate_ESS_ENCLOSURE_CAPEX();
		calculate_ESS_ENCLOSURE_DISPOSAL();

		calculate_PVpanel_CAPEX();
		calculate_PVBoP_CAPEX();
		calculate_PVroof_CAPEX();
		calculate_PVground_CAPEX();

		calculate_EV_CP_cost();
		calculate_EV_CP_install();

		calculate_Grid_CAPEX();

		calculate_ASHP_CAPEX(mTaskData.ASHP_HPower);

		float ESS_CAPEX = mESS_PCS_CAPEX + mESS_ENCLOSURE_CAPEX + mESS_ENCLOSURE_DISPOSAL;
		float PV_CAPEX = mPVpanel_CAPEX + mPVBoP_CAPEX + mPVroof_CAPEX + mPVground_CAPEX;
		float EV_CP_CAPEX = mEV_CP_cost + mEV_CP_install;
		float ASHP_CAPEX = mASHP_CAPEX;
		float Grid_CAPEX = mGrid_CAPEX;

		float Project_cost = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX) * mProject_plan_develop_EPC;
		float Project_cost_grid = Grid_CAPEX * mProject_plan_develop_Grid;

		mProject_CAPEX = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX + Project_cost + Project_cost_grid);
	}

	
	void calculateCosts_no_CAPEX(const CostVectors& costVectors) {

		//	This function is an alterntive to calculateCosts() without CAPEX if CAPEX is already calculated earlier in Simulate.cpp
		// 
				// need to add a new config parameter here
		const float IMPORT_FUEL_PRICE = 12.2f;
		const float BOILER_EFFICIENCY = 0.9f;

		const int s7_EV_CP_number = mTaskData.s7_EV_CP_number;
		const int f22_EV_CP_number = mTaskData.f22_EV_CP_number;
		const int r50_EV_CP_number = mTaskData.r50_EV_CP_number;
		const int u150_EV_CP_number = mTaskData.u150_EV_CP_number;
		const float kw_grid_upgrade = mkW_Grid;
		const float heatpump_power_capacity = mTaskData.ASHP_HPower;

		//calculate_ESS_PCS_CAPEX(mESS_kW);
		calculate_ESS_PCS_OPEX();
		//calculate_ESS_ENCLOSURE_CAPEX(mESS_kWh);
		calculate_ESS_ENCLOSURE_OPEX();
		//calculate_ESS_ENCLOSURE_DISPOSAL(mESS_kWh);

		//calculate_PVpanel_CAPEX(mPV_kWp_total);
		//calculate_PVBoP_CAPEX(mPV_kWp_total);
		//calculate_PVroof_CAPEX(mPV_kWp_total);
		//calculate_PVground_CAPEX(mPV_kWp_total);
		calculate_PV_OPEX();

		//calculate_EV_CP_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number);
		//calculate_EV_CP_install(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number);

		//calculate_Grid_CAPEX(kw_grid_upgrade);

		//calculate_ASHP_CAPEX(heatpump_power_capacity);


		calculate_total_annualised_cost(mESS_kW, mTaskData.ESS_capacity, mPV_kWp_total, s7_EV_CP_number,
			f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number, kw_grid_upgrade, heatpump_power_capacity);


		// for now, simply fix export price
		year_TS export_elec_prices{ Eigen::VectorXf::Constant(mTaskData.calculate_timesteps(), mTaskData.Export_kWh_price) };
		// year_TS baseline_elec_load = eload.getTotalBaselineFixLoad() + grid.getActualLowPriorityLoad() + MountBESS.getAuxLoad() + eload.getActual_Data_Centre_load(); // depreciated in V 08 due to simplified baselining
		year_TS baseline_elec_load = costVectors.building_load_e;

		calculate_baseline_elec_cost(baseline_elec_load);

		//year_TS baseline_heat_load = hload.getHeatload() + grid.getActualLowPriorityLoad(); // depreciated in V 08 due to simplified baselining

		year_TS baseline_heat_load = costVectors.heatload_h;

		year_TS import_fuel_prices{ Eigen::VectorXf::Constant(mTaskData.calculate_timesteps(), IMPORT_FUEL_PRICE) };

		calculate_baseline_fuel_cost(baseline_heat_load, import_fuel_prices, BOILER_EFFICIENCY);

		calculate_scenario_elec_cost(costVectors.grid_import_e);
		calculate_scenario_fuel_cost(costVectors.heat_shortfall_h, import_fuel_prices);
		calculate_scenario_export_cost(costVectors.grid_export_e, export_elec_prices);

		calculate_scenario_EV_revenue(costVectors.actual_ev_load_e);
		calculate_scenario_HP_revenue(costVectors.actual_data_centre_load_e);
		calculate_scenario_LP_revenue(costVectors.actual_low_priority_load_e);


		calculate_scenario_cost_balance(mTotal_annualised_cost);

		//========================================

		//calculate_Project_CAPEX(mESS_kW, mTaskData.ESS_capacity, mPV_kWp_total, s7_EV_CP_number,
		//	f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number, kw_grid_upgrade, heatpump_power_capacity);

		//========================================

		calculate_payback_horizon();

		//========================================

		// Calculate time_dependent CO2e operational emissions section

		calculate_baseline_elec_CO2e(baseline_elec_load);

		calculate_baseline_fuel_CO2e(baseline_heat_load);

		calculate_scenario_elec_CO2e(costVectors.grid_import_e);

		calculate_scenario_fuel_CO2e(costVectors.heat_shortfall_h);

		calculate_scenario_export_CO2e(costVectors.grid_export_e);

		calculate_scenario_LP_CO2e(costVectors.actual_low_priority_load_e);

		calculate_scenario_carbon_balance();
	}



	//ESS COSTS

	// these functions account for headroom built in to Grid_connection to take import/export power peaks intratimestep
	void calculate_ESS_PCS_CAPEX() {
		
		if (mESS_kWmin == 0 || mTaskData.ESS_capacity == 0) // either of these is zero - not an ESS so no cost!
		{
			mESS_PCS_CAPEX = 0;
			return;
		}
		else
		{
			// thresholds in kW units
			float small_thresh = 50;
			float mid_thresh = 1000;

			// costs in £ / kW
			float small_cost = 250.0;
			float mid_cost = 125.0;
			float large_cost = 75.0;

			if (mESS_kW < small_thresh) {
				mESS_PCS_CAPEX = small_cost * mESS_kW;
			}
			else if (small_thresh <= mESS_kW && mESS_kW <= mid_thresh) {
				mESS_PCS_CAPEX = (small_cost * small_thresh) + ((mESS_kW - small_thresh) * mid_cost);
			}
			else if (mESS_kW > mid_thresh) {
				mESS_PCS_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mESS_kW - small_thresh - mid_thresh) * large_cost);
			}

			return;
		}
	}

	void calculate_ESS_PCS_OPEX() {

		if (mESS_kWmin == 0 || mTaskData.ESS_capacity == 0) // either of these is zero - not an ESS so no cost!
		{
			mESS_PCS_OPEX = 0;
			return;
		}
		else
		{

			// threholds in kW units
			float small_thresh = 50;
			float mid_thresh = 1000;

			// costs in £ / kW
			float small_cost = 8.0;
			float mid_cost = 4.0;
			float large_cost = 1.0;

			

			if (mESS_kW < small_thresh) {
				mESS_PCS_OPEX = small_cost * mESS_kW;
			}
			else if (small_thresh <= mESS_kW && mESS_kW <= mid_thresh) {
				mESS_PCS_OPEX = (small_cost * small_thresh) + ((mESS_kW - small_thresh) * mid_cost);
			}
			else if (mESS_kW > mid_thresh) {
				mESS_PCS_OPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mESS_kW - small_thresh - mid_thresh) * large_cost);
			}

			return;
		}
	}

	void calculate_ESS_ENCLOSURE_CAPEX() {

		if (mESS_kWmin == 0 || mTaskData.ESS_capacity == 0) // either of these is zero - not an ESS so no cost!
		{
			mESS_ENCLOSURE_CAPEX = 0;
			return;
		}
		else
		{
			// threholds in kW units
			float small_thresh = 100;
			float mid_thresh = 2000;

			// costs in £ / kWh
			float small_cost = 480.0;
			float mid_cost = 360.0;
			float large_cost = 300.0;

			

			if (mESS_kWh < small_thresh) {
				mESS_ENCLOSURE_CAPEX = small_cost * mESS_kWh;
			}
			else if (small_thresh <= mESS_kWh && mESS_kWh <= mid_thresh) {
				mESS_ENCLOSURE_CAPEX = (small_cost * small_thresh) + ((mESS_kWh - small_thresh) * mid_cost);
			}
			else if (mESS_kWh > mid_thresh) {
				mESS_ENCLOSURE_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mESS_kWh - small_thresh - mid_thresh) * large_cost);
			}
			
		}
		return;
	}

	void calculate_ESS_ENCLOSURE_OPEX() {

		if (mESS_kWmin == 0 || mTaskData.ESS_capacity == 0) // either of these is zero - not an ESS so no cost!
		{
			 mESS_ENCLOSURE_OPEX = 0;
			return;
		}
		else
		{
			// threholds in kWh units
			float small_thresh = 100;
			float mid_thresh = 2000;

			// costs in £ / kWh
			float small_cost = 10.0;
			float mid_cost = 4.0;
			float large_cost = 2.0;

			if (mESS_kWh < small_thresh) {
				mESS_ENCLOSURE_OPEX = small_cost * mESS_kWh;
			}
			else if (small_thresh <= mESS_kWh && mESS_kWh <= mid_thresh) {
				mESS_ENCLOSURE_OPEX = (small_cost * small_thresh) + ((mESS_kWh - small_thresh) * mid_cost);
			}
			else if (mESS_kWh > mid_thresh) {
				mESS_ENCLOSURE_OPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mESS_kWh - small_thresh - mid_thresh) * large_cost);
			}
			return;
		}
	}

	// thresholds in kWh units
	void calculate_ESS_ENCLOSURE_DISPOSAL() {
		if (mESS_kWmin == 0 || mTaskData.ESS_capacity == 0) // either of these is zero - not an ESS so no cost!
		{
			mESS_ENCLOSURE_DISPOSAL = 0;
			return;
		}

		float small_thresh = 100;
		float mid_thresh = 2000;

		// costs in £ / kWh
		float small_cost = 30.0;
		float mid_cost = 20.0;
		float large_cost = 15.0;

		

		if (mESS_kWh < small_thresh) {
			mESS_ENCLOSURE_DISPOSAL = small_cost * mESS_kWh;
		} else if (small_thresh <= mESS_kWh && mESS_kWh <= mid_thresh) {
			mESS_ENCLOSURE_DISPOSAL = (small_cost * small_thresh) + ((mESS_kWh - small_thresh) * mid_cost);
		} else if (mESS_kWh > mid_thresh) {
			mESS_ENCLOSURE_DISPOSAL = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mESS_kWh - small_thresh - mid_thresh) * large_cost);
		}

		return;
	}

	//PHOTOVOLTAIC COSTS (All units of kWp are DC)

	void calculate_PVpanel_CAPEX() {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW DC
		float small_cost = 150.0;
		float mid_cost = 110.0;
		float large_cost = 95.0;


		if (mPV_kWp_total < small_thresh) {
			mPVpanel_CAPEX = small_cost * mPV_kWp_total;
		} else if (small_thresh <= mPV_kWp_total && mPV_kWp_total <= mid_thresh) {
			mPVpanel_CAPEX = (small_cost * small_thresh) + ((mPV_kWp_total - small_thresh) * mid_cost);
		} else if (mPV_kWp_total > mid_thresh) {
			mPVpanel_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mPV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return;
	}

	void calculate_PVBoP_CAPEX() {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 120.0;
		float mid_cost = 88.0;
		float large_cost = 76.0;

		if (mPV_kWp_total < small_thresh) {
			mPVBoP_CAPEX = small_cost * mPV_kWp_total;
		} else if (small_thresh <= mPV_kWp_total && mPV_kWp_total <= mid_thresh) {
			mPVBoP_CAPEX = (small_cost * small_thresh) + ((mPV_kWp_total - small_thresh) * mid_cost);
		} else if (mPV_kWp_total > mid_thresh) {
			mPVBoP_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mPV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return;
	}

	void calculate_PVroof_CAPEX() {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 250.0;
		float mid_cost = 200.0;
		float large_cost = 150.0;

		if (mPV_kWp_roof < small_thresh) {
			mPVroof_CAPEX = small_cost * mPV_kWp_roof;
		} else if (small_thresh <= mPV_kWp_roof && mPV_kWp_roof <= mid_thresh) {
			mPVroof_CAPEX = (small_cost * small_thresh) + ((mPV_kWp_roof - small_thresh) * mid_cost);
		} else if (mPV_kWp_roof > mid_thresh) {
			mPVroof_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mPV_kWp_roof - small_thresh - mid_thresh) * large_cost);
		}

		return;
	}

	void calculate_PVground_CAPEX() {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 150.0; 
		float mid_cost = 125.0;
		float large_cost = 100.0;

		if (mPV_kWp_ground < small_thresh) {
			mPVground_CAPEX = small_cost * mPV_kWp_ground;
		} else if (small_thresh <= mPV_kWp_ground && mPV_kWp_ground <= mid_thresh) {
			mPVground_CAPEX = (small_cost * small_thresh) + ((mPV_kWp_ground - small_thresh) * mid_cost);
		} else if (mPV_kWp_ground > mid_thresh) {
			mPVground_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mPV_kWp_ground - small_thresh - mid_thresh) * large_cost);
		}

		return;
	}

	void calculate_PV_OPEX() {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kWp DC
		float small_cost = 2.0;
		float mid_cost = 1.0;
		float large_cost = 0.50;

		if (mPV_kWp_total < small_thresh) {
			mPV_OPEX = small_cost * mPV_kWp_total;
		} else if (small_thresh <= mPV_kWp_total && mPV_kWp_total <= mid_thresh) {
			mPV_OPEX = (small_cost * small_thresh) + ((mPV_kWp_total - small_thresh) * mid_cost);
		} else if (mPV_kWp_total > mid_thresh) {
			mPV_OPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mPV_kWp_total - small_thresh - mid_thresh) * large_cost);
		}

		return;
	}

	// EV charge point costs 

	// Cost model for EV charge points is based on per unit of each charger type, 7 kW, 22 kW, 50 kW and 150 kW

	void calculate_EV_CP_cost() {
		// costs in £ / unit (1 hd unit 2 connectors)
		float s7_EV_cost = 1200.00;
		float f22_EV_cost = 2500.00;
		float r50_EV_cost = 20000.00;
		float u150_EV_cost = 60000.00;

		 mEV_CP_cost = (float(mTaskData.s7_EV_CP_number) * s7_EV_cost) 
			 + (float(mTaskData.f22_EV_CP_number) * f22_EV_cost)
			 + (float(mTaskData.r50_EV_CP_number) * r50_EV_cost)
			 + (float(mTaskData.u150_EV_CP_number) * u150_EV_cost);

		return;
	}

	void calculate_EV_CP_install() {
		// costs in £ / unit (1 hd unit 2 connectors)
		float s7_EV_install = 600.00;
		float f22_EV_install = 1000.00;
		float r50_EV_install = 3000.00;
		float u150_EV_install = 10000.00;

		mEV_CP_install = (float(mTaskData.s7_EV_CP_number) * s7_EV_install) 
			+ (float(mTaskData.f22_EV_CP_number) * f22_EV_install)
			+ (float(mTaskData.r50_EV_CP_number) * r50_EV_install)
			+ (float(mTaskData.u150_EV_CP_number) * u150_EV_install);

		return;
	}

	// Grid upgrade costs

	void calculate_Grid_CAPEX() {
		float small_thresh = 50;
		float mid_thresh = 1000;

		// costs in £ / kW DC
		float small_cost = 240.0;
		float mid_cost = 160.0;
		float large_cost = 120.0;

		if (mkW_Grid < small_thresh) {
			mGrid_CAPEX = small_cost * mkW_Grid;
		} else if (small_thresh <= mkW_Grid && mkW_Grid <= mid_thresh) {
			mGrid_CAPEX = (small_cost * small_thresh) + ((mkW_Grid - small_thresh) * mid_cost);
		} else if (mkW_Grid > mid_thresh) {
			mGrid_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((mkW_Grid - small_thresh - mid_thresh) * large_cost);
		}

		return;
	}

	// ASHP CAPEX costs

	void calculate_ASHP_CAPEX(float heatpump_power_capacity) {
		float small_thresh = 10;
		float mid_thresh = 100;

		// costs in £ / kW DC
		float small_cost = 1000.0;
		float mid_cost = 1000.0;
		float large_cost = 1000.0;

		if (heatpump_power_capacity < small_thresh) {
			mASHP_CAPEX = small_cost * heatpump_power_capacity;
		} else if (small_thresh <= heatpump_power_capacity && heatpump_power_capacity <= mid_thresh) {
			mASHP_CAPEX = (small_cost * small_thresh) + ((heatpump_power_capacity - small_thresh) * mid_cost);
		} else if (heatpump_power_capacity > mid_thresh) {
			mASHP_CAPEX = (small_cost * small_thresh) + (mid_cost * mid_thresh) + ((heatpump_power_capacity - small_thresh - mid_thresh) * large_cost);
		}

		return;
	}

	float calculate_ESS_annualised_cost() const {
		float ESS_annualised_cost = (mESS_PCS_CAPEX + mESS_ENCLOSURE_CAPEX + mESS_ENCLOSURE_DISPOSAL) / mESS_lifetime + mESS_PCS_OPEX + mESS_ENCLOSURE_OPEX;
		return ESS_annualised_cost;
	}

	float calculate_PV_annualised_cost() const {
		float PV_annualised_cost = ((mPVpanel_CAPEX + mPVBoP_CAPEX + mPVroof_CAPEX + mPVground_CAPEX) / mPV_panel_lifetime) + mPV_OPEX;
		return PV_annualised_cost;
	}

	float calculate_EV_CP_annualised_cost(int s7_EV_CP_number, 
		int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number) const {
		float EV_CP_annualised_cost = 
			(
			mEV_CP_cost + mEV_CP_install
			) / mEV_CP_lifetime;

		return EV_CP_annualised_cost;
	}

	float calculate_ASHP_annualised_cost(float heatpump_power_capacity) const {
		float ASHP_annualised_cost = mASHP_CAPEX/ mASHP_lifetime;
		return ASHP_annualised_cost;
	}

	float calculate_Grid_annualised_cost(float kw_grid_upgrade) const {
		float Grid_annualised_cost = mGrid_CAPEX/ mGrid_lifetime;
		return Grid_annualised_cost;
	}

	float calculate_Project_annualised_cost(float ESS_kW, float ESS_kWh, float PV_kWp_total, int s7_EV_CP_number, 
		int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number, float kw_grid_upgrade, float heatpump_power_capacity) const {

		float ESS_CAPEX = mESS_PCS_CAPEX + mESS_ENCLOSURE_CAPEX + mESS_ENCLOSURE_DISPOSAL;
		float PV_CAPEX = mPVpanel_CAPEX + mPVBoP_CAPEX + mPVroof_CAPEX + mPVground_CAPEX;
		float EV_CP_CAPEX = mEV_CP_cost + mEV_CP_install;
		float ASHP_CAPEX = mASHP_CAPEX;
		float Grid_CAPEX = mGrid_CAPEX;

		float Project_cost = (ESS_CAPEX + PV_CAPEX + EV_CP_CAPEX + ASHP_CAPEX) * mProject_plan_develop_EPC;
		float Project_cost_grid = Grid_CAPEX * mProject_plan_develop_Grid;

		float Project_annualised_cost = (Project_cost + Project_cost_grid) / mProject_lifetime;

		return Project_annualised_cost;
	}

	// Calculate annualised costs

	void calculate_total_annualised_cost(float ESS_kW, float ESS_kWh, float PV_kWp_total, int s7_EV_CP_number, 
		int f22_EV_CP_number, int r50_EV_CP_number, int u150_EV_CP_number, float kw_grid_upgrade, float heatpump_power_capacity) {

		float ESS_annualised_cost = ((mESS_PCS_CAPEX + mESS_ENCLOSURE_CAPEX + mESS_ENCLOSURE_DISPOSAL) / mESS_lifetime) + mESS_PCS_OPEX + mESS_ENCLOSURE_OPEX;
		
		float PV_annualised_cost = ((mPVpanel_CAPEX + mPVBoP_CAPEX + mPVroof_CAPEX + mPVground_CAPEX) / mPV_panel_lifetime) + mPV_OPEX;

		float EV_CP_annualised_cost = calculate_EV_CP_annualised_cost(s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number);

		float Grid_annualised_cost = calculate_Grid_annualised_cost(kw_grid_upgrade);

		float ASHP_annualised_cost = calculate_ASHP_annualised_cost(heatpump_power_capacity);

		float Project_annualised_cost = calculate_Project_annualised_cost(ESS_kW, ESS_kWh, PV_kWp_total, s7_EV_CP_number, f22_EV_CP_number, r50_EV_CP_number, u150_EV_CP_number, kw_grid_upgrade, heatpump_power_capacity);

		mTotal_annualised_cost = Project_annualised_cost + ESS_annualised_cost + PV_annualised_cost + EV_CP_annualised_cost + Grid_annualised_cost + ASHP_annualised_cost;
	}

	// time-dependent scenario costs

	void calculate_baseline_elec_cost(const year_TS& baseline_elec_load) {

		year_TS mBaseline_elec_cost_TS = (baseline_elec_load.array() * mImport_prices.array()); 
		mBaseline_elec_cost = mBaseline_elec_cost_TS.sum();
	};

	void calculate_baseline_fuel_cost(const year_TS& baseline_heat_load, const year_TS& import_fuel_prices, float boiler_efficiency) {
		float baseline_heat_load_sum = baseline_heat_load.sum();

		mBaseline_fuel_cost = (baseline_heat_load_sum * import_fuel_prices[0] / boiler_efficiency) / 100; // this should be changed to divided by boiler efficiency
	};

	void calculate_scenario_elec_cost(const year_TS& grid_import) {

		year_TS mScenario_import_cost_TS = (grid_import.array() * mImport_prices.array());
		mScenario_import_cost = mScenario_import_cost_TS.sum(); // just use fixed value for now
	};

	void calculate_scenario_fuel_cost(const year_TS& total_heat_shortfall, const year_TS& import_fuel_prices) {
		float total_heat_shortfall_sum = total_heat_shortfall.sum();

		mScenario_fuel_cost = (total_heat_shortfall_sum * import_fuel_prices[0] / mBoiler_efficiency) / 100; // this should be changed to divided by boiler efficiency
	};

	void calculate_scenario_export_cost(const year_TS& grid_export, const year_TS& export_elec_prices) {
		
		// just use fixed value for now
		year_TS mScenario_export_cost_TS = (-grid_export.array() * (export_elec_prices.array()/100));
		mScenario_export_cost = mScenario_export_cost_TS.sum();
	};

	void calculate_scenario_EV_revenue(const year_TS& actual_ev_load) {
		year_TS mScenario_EV_revenueTS = actual_ev_load.array() * mEV_low_price; // will need to separate out EV charge tariffs later, assume all destination charging for no
		mScenario_EV_revenue = mScenario_EV_revenueTS.sum();
	};

	void calculate_scenario_HP_revenue(const year_TS& actual_data_centre_load) {
		year_TS mScenario_HP_revenueTS = actual_data_centre_load.array() * mHP_price;
		mScenario_HP_revenue = mScenario_HP_revenueTS.sum();
	};

	void calculate_scenario_LP_revenue(const year_TS& actual_low_priority_load) {
		mLP_price = mMains_gas_price/mBoiler_efficiency;
		year_TS mScenario_LP_revenueTS = actual_low_priority_load.array() * mLP_price; // will need to separate out EV charge tariffs later, assume all destination charging for no
		mScenario_LP_revenue = mScenario_LP_revenueTS.sum();
	}


	void calculate_scenario_cost_balance(float Total_annualised_cost) {
		mScenario_cost_balance = (mBaseline_elec_cost + mBaseline_fuel_cost) - (mScenario_import_cost + mScenario_fuel_cost + mScenario_export_cost - mScenario_EV_revenue - mScenario_HP_revenue - mScenario_LP_revenue + Total_annualised_cost);
	};

	void calculate_payback_horizon() {
		if (mScenario_cost_balance > 0) {
			mPayback_horizon_years = mProject_CAPEX / mScenario_cost_balance;
		} else {
			// a non-positive scenario_cost_balance indicates that there is no payback horizon
			mPayback_horizon_years = std::numeric_limits<float>::max();
		}
	};


	// Member functions to calculate CO2 equivalent operational emissions costs

	void calculate_baseline_elec_CO2e(const year_TS& baseline_elec_load) {
		float baseline_elec_load_sum = baseline_elec_load.sum();

		// just use fixed value for now
		mBaseline_elec_CO2e = (baseline_elec_load_sum * mSupplier_electricity_kg_CO2e); 
	};

	void calculate_baseline_fuel_CO2e(const year_TS& baseline_heat_load) {
		float baseline_heat_load_sum = baseline_heat_load.sum();

		mBaseline_fuel_CO2e = (baseline_heat_load_sum * mLPG_kg_C02e);/// mBoiler_efficiency; // AS to confirm whether to multiply by boilerefficiency or not but M-VEST v-06 does not as per !COSTX6 "(well2heat)"
	};

	void calculate_scenario_elec_CO2e(const year_TS& grid_import) {
		float grid_import_sum = grid_import.sum();

		// just use fixed value for now
		mScenario_elec_CO2e = (grid_import_sum * mSupplier_electricity_kg_CO2e);
	};

	void calculate_scenario_fuel_CO2e(const year_TS& total_heat_shortfall) {
		float total_heat_shortfall_sum = total_heat_shortfall.sum();

		mScenario_fuel_CO2e = (total_heat_shortfall_sum * mLPG_kg_C02e);// / mBoiler_efficiency; // AS to confirm whether to multiply by boilerefficiency or not but M-VEST v-06 does not as per !COSTX6 "(well2heat)"
	};

	void calculate_scenario_export_CO2e(const year_TS& grid_export) {
		float grid_export_sum = grid_export.sum();

		mScenario_export_CO2e = (-grid_export_sum * mSupplier_electricity_kg_CO2e);
	};

	void calculate_scenario_LP_CO2e(const year_TS& actual_low_priority_load) {
	
		year_TS mScenario_LP_CO2eTS = actual_low_priority_load.array() * mMains_gas_kg_C02e; // will need to separate out EV charge tariffs later, assume all destination charging for no
		mScenario_LP_CO2e =  -mScenario_LP_CO2eTS.sum();
	}


	void calculate_scenario_carbon_balance() {
		mScenario_carbon_balance = (mBaseline_elec_CO2e + mBaseline_fuel_CO2e) - (mScenario_elec_CO2e + mScenario_fuel_CO2e + mScenario_export_CO2e + mScenario_LP_CO2e);
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

	float get_PV_kWp_total() const {
		return mPV_kWp_total;
	}

	float get_ESS_kW() const {
		return mESS_kW;
	}

	float get_ESS_kWmin() const {
		return mESS_kWmin;
	}

	float get_Baseline_elec_cost() const {
		return mBaseline_elec_cost;
	}

	float get_Baseline_fuel_cost() const {
		return mBaseline_fuel_cost;
	}

	float get_Baseline_elec_CO2e() const {
		return mBaseline_elec_CO2e;
	}

	float get_Baseline_fuel_CO2e() const {
		return mBaseline_fuel_CO2e;
	}


	float get_Scenario_import_cost() const {
		return mScenario_import_cost;
	}

	float get_Scenario_fuel_cost() const {
		return mScenario_fuel_cost;
	}

	float get_Scenario_export_cost() const {
		return mScenario_export_cost;
	}

	float get_Scenario_elec_CO2e() const{
		return mScenario_elec_CO2e;
	}

	float get_Scenario_fuel_CO2e() const{
		return mScenario_fuel_CO2e;
	}

	float get_Scenario_export_CO2e() const{
		return mScenario_export_CO2e;
	}

	float get_Scenario_LP_CO2e() const {
		return mScenario_LP_CO2e;
	}

	float get_Scenario_EV_revenue() const {
		return mScenario_EV_revenue;
	}

	float  get_Scenario_HP_revenue() const {
		return mScenario_HP_revenue;
	};

	float  get_Scenario_LP_revenue() const {
		return mScenario_LP_revenue;
	};
	float get_ESS_PCS_CAPEX() const {
		return mESS_PCS_CAPEX;
	}

	float get_ESS_PCS_OPEX() const {
		return mESS_PCS_OPEX;
	}

	float get_ESS_ENCLOSURE_CAPEX() const {
		return mESS_ENCLOSURE_CAPEX;
	}

	float get_ESS_ENCLOSURE_OPEX() const {
		return mESS_ENCLOSURE_OPEX;
	}

	float get_ESS_ENCLOSURE_DISPOSAL() const {
		return mESS_ENCLOSURE_DISPOSAL;
	}

	float get_PVpanel_CAPEX() const {
		return mPVpanel_CAPEX;
	}

	float get_PVBoP_CAPEX() const {
		return mPVBoP_CAPEX;
	}

	float get_PVroof_CAPEX() const {
		return mPVroof_CAPEX;
	}

	float get_PVground_CAPEX() const {
		return mPVground_CAPEX;
	}

	float get_PV_OPEX() const {
		return mPV_OPEX;
	}

	float get_EV_CP_cost() const {
		return mEV_CP_cost;
	}

	float get_EV_CP_install() const {
		return mEV_CP_install;
	}

	float get_Grid_CAPEX() const {
		return mGrid_CAPEX;
	}

	float get_ASHP_CAPEX() const {
		return mASHP_CAPEX;
	}


	// "hard wired" constants for the moment
	private:
		const TaskData& mTaskData;

		// coefficient applied to local infrastructure CAPEX (decimal, not percentage)
		const float mProject_plan_develop_EPC = 0.1f; 
		// coefficient applied to grid infrastructure CAPEX (decimal, not percentage)
		const float mProject_plan_develop_Grid = 0.1f; 

		const float mMains_gas_kg_C02e = 0.201f; // kg/kWh(w2h) 
		const float mLPG_kg_C02e = 0.239f; // kg/kWh (well2heat)
		// every kWh that goes into an EV saves this much on the counterfactual of an ICE petrol vehicle
		const float mPetrol_displace_kg_CO2e = 0.9027f;

		// coefficient applied to convert gas kWh to heat kWh (decimal, not percentage)
		const float mBoiler_efficiency = 0.9f; 
		const float mMains_gas_price = 0.068f; // £/kWh  
		const float mLPG_cost_price = 0.122f; // £/kWh

		const float mSupplier_electricity_kg_CO2e = 0.182f; //

		year_TS mImport_prices;

		// site price

		float mEV_low_price = 0.45f; // £/kWh site price for destination EV charging, 22 kW and below
		float mEV_high_price = 0.79f; //£/kWh site price for high power EV charging, 50 KW and above
		float mHP_price = 0.50f; // £/kWh site price for data centre compute (hi priority load)
		float mLP_price ; // assume this is just the equivalent fossil fuel derived heat


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

		float mScenario_LP_CO2e;

		float mScenario_carbon_balance;

		float mScenario_EV_revenue;

		float mScenario_HP_revenue;

		float mScenario_LP_revenue;

		// internal variables used in the cost calculation

		float mPV_kWp_total;
		float mPV_kWp_ground;
		float mPV_kWp_roof;

		float mESS_kW;
		float mESS_kWh;
		float mESS_kWmin;

		float mkW_Grid;

		// asset costs 

		float mESS_PCS_CAPEX;
		float mESS_PCS_OPEX;
		float mESS_ENCLOSURE_CAPEX;
		float mESS_ENCLOSURE_OPEX;
		float mESS_ENCLOSURE_DISPOSAL;

		float mPVpanel_CAPEX;
		float mPVBoP_CAPEX;
		float mPVroof_CAPEX;
		float mPVground_CAPEX;
		float mPV_OPEX;

		float mEV_CP_cost;
		float mEV_CP_install;

		float mGrid_CAPEX;

		float mASHP_CAPEX;

		
};


#include "Simulate.hpp"

#include <chrono>
#include <iostream>
#include <limits> 

#include <Eigen/Core>

#include "Assets.hpp"
#include "TaskData.hpp"
#include "Eload.hpp"
#include "Grid.hpp"
#include "Hload.hpp"
#include "Costs.hpp"
#include "HotWcylA_cl.hpp"

//#include "Grid3.hpp"
//#include "ESS2.hpp"
//#include "Battery.hpp"

Simulator::Simulator() {

}


FullSimulationResult Simulator::simulateScenarioFull(const HistoricalData& historicalData, const TaskData& taskData, SimulationType simulationType) const {
	/*CALCULATIVE SECTION - START PROFILING */
	auto start = std::chrono::high_resolution_clock::now(); //start runtime clock


	// Calculate CAPEX upfront to discard scenarios above CAPEX contraint early 
	Costs myCost(taskData);
	myCost.calculate_Project_CAPEX(myCost.get_ESS_kW(), taskData.ESS_capacity, myCost.get_PV_kWp_total(), taskData.s7_EV_CP_number, taskData.f22_EV_CP_number, taskData.r50_EV_CP_number, taskData.u150_EV_CP_number, 0, taskData.ASHP_HPower);
	if (taskData.CAPEX_limit*1000 < myCost.get_project_CAPEX())
	{
		// TODO - apply proper fix for 'nullable' results
		FullSimulationResult fullSimulationResult;
		fullSimulationResult.paramIndex = taskData.paramIndex;
		fullSimulationResult.project_CAPEX = myCost.get_project_CAPEX();

		fullSimulationResult.total_annualised_cost = std::numeric_limits<float>::max();
		fullSimulationResult.scenario_cost_balance = std::numeric_limits<float>::min();
		fullSimulationResult.payback_horizon_years = std::numeric_limits<float>::max();
		fullSimulationResult.scenario_carbon_balance = std::numeric_limits<float>::min();
		return fullSimulationResult;
	}

	year_TS RGen_total = calculateRGenTotal(historicalData, taskData);

	Hload MountHload{ historicalData, taskData }; // initialise Hload based on historical data and taskdata
	Grid MountGrid{ taskData }; //initialise Grid based on taskdata

	MountHload.performHeatCalculations(historicalData, taskData);
	
	Eload MountEload{historicalData, taskData }; // initialise Eload based on historical data and taskdata

	HotWcylA_cl HotWaterCyl{ historicalData, taskData }; // initialise Hotwater cylinder based on taskData

	ESS MountBESS{ taskData }; //initialise ESS based on taskdata

	MountEload.calculateLoads(MountHload, MountBESS, RGen_total, taskData);
	
	year_TS ESUM = MountEload.getTotal_target_load_fixed_flex() - RGen_total;

	// non balancing actions for stateful components

	HotWaterCyl.AllCalcs(ESUM); // this will be TempSum in V08

	ESUM += HotWaterCyl.getDHW_Charging(); // add the DHW electrical charging loads from ESUM 

	// in V08 we will split DHW charging load sent to TempSum between Heat pump () heating load and instantaneous electric heating (HotWaterCyl.getDHW_diverter() + HotWaterCyl.getDHW_shortfall());

	MountBESS.initialise(ESUM[0]);
	MountBESS.runTimesteps(ESUM);

	MountGrid.performGridCalculations(ESUM, MountBESS, MountHload, MountEload.getHeadroomL1());

	MountEload.calculateElectricHeat(MountGrid, MountHload, taskData);

	MountHload.calculateHeatSUM(MountEload.getData_Centre_HP_load_scalar(), MountGrid.getActualLowPriorityLoad());

	myCost.calculateCosts_no_CAPEX(MountEload, MountHload, MountGrid, MountBESS); // CAPEX calc now at beginning

	//Data reporting

	FullSimulationResult fullSimulationResult;

	if (simulationType == SimulationType::FullReporting) {
		fullSimulationResult.Rgen_total = RGen_total;
		fullSimulationResult.Total_load = MountEload.getTotalLoad();
		fullSimulationResult.ESUM = ESUM;
		fullSimulationResult.ESS_available_discharge_power = MountBESS.getESSAvailableDischargePower();;
		fullSimulationResult.ESS_available_charge_power = MountBESS.getESSAvailableChargePower();
		fullSimulationResult.ESS_Rgen_only_charge = MountBESS.getESSRgenOnlyCharge();
		fullSimulationResult.ESS_discharge = MountBESS.getESSDischarge();
		fullSimulationResult.ESS_charge = MountBESS.getESSCharge();
		fullSimulationResult.ESS_resulting_SoC = MountBESS.getESSResultingSoC();
		fullSimulationResult.Pre_grid_balance = MountGrid.getPreGridBalance();
		fullSimulationResult.Grid_Import = MountGrid.getGridImport();
		fullSimulationResult.Grid_Export = MountGrid.getGridExport();
		fullSimulationResult.Post_grid_balance = MountGrid.getPostGridBalance();
		fullSimulationResult.Pre_flex_import_shortfall = MountGrid.getPreFlexImportShortfall();
		fullSimulationResult.Pre_Mop_curtailed_export = MountGrid.getPreMopCurtailedExport();
		fullSimulationResult.Actual_import_shortfall = MountGrid.getActualImportShortfall();
		fullSimulationResult.Actual_curtailed_export = MountGrid.getActualCurtailedExport();
		fullSimulationResult.Actual_high_priority_load = MountGrid.getActualHighPriorityLoad();
		fullSimulationResult.Actual_low_priority_load = MountGrid.getActualLowPriorityLoad();
		fullSimulationResult.Heatload = historicalData.heatload_data;
		fullSimulationResult.DHW_load = historicalData.DHWdemand_data;
		fullSimulationResult.DHW_charging = HotWaterCyl.getDHW_Charging();
		fullSimulationResult.DHW_SoC = HotWaterCyl.getDHW_SoC_history();
		fullSimulationResult.DHW_Standby_loss = HotWaterCyl.getDHW_standby_losses();
		fullSimulationResult.DHW_ave_temperature = HotWaterCyl.getDHW_ave_temperature();
		fullSimulationResult.DHW_Shortfall = HotWaterCyl.getDHW_shortfall();
		fullSimulationResult.Scaled_heatload = MountHload.getHeatload();
		fullSimulationResult.Electrical_load_scaled_heat_yield = MountHload.getElectricalLoadScaledHeatYield();
		fullSimulationResult.Heat_shortfall = MountHload.getHeatShortfall();
		fullSimulationResult.Heat_surplus = MountHload.getEHeatSurplus();
		
		fullSimulationResult.Baseline_electricity_cost = myCost.get_Baseline_elec_cost();
		fullSimulationResult.Baseline_fuel_cost = myCost.get_Baseline_fuel_cost();

		fullSimulationResult.Baseline_electricity_carbon = myCost.get_Baseline_elec_CO2e();
		fullSimulationResult.Baseline_fuel_carbon = myCost.get_Baseline_fuel_CO2e();

		fullSimulationResult.Scenario_electricity_cost = myCost.get_Scenario_import_cost();
		fullSimulationResult.Scenario_fuel_cost = myCost.get_Scenario_fuel_cost();
		fullSimulationResult.Scenario_grid_export_cost = myCost.get_Scenario_export_cost();
		
		fullSimulationResult.Scenario_electricity_carbon = myCost.get_Scenario_elec_CO2e();
		fullSimulationResult.Scenario_fuel_carbon = myCost.get_Scenario_fuel_CO2e();
		fullSimulationResult.Scenario_grid_export_carbon = myCost.get_Scenario_export_CO2e();
		fullSimulationResult.Scenario_avoided_fuel_carbon = myCost.get_Scenario_LP_CO2e();

		fullSimulationResult.Resulting_EV_charge_revenue = myCost.get_Scenario_EV_revenue();
		fullSimulationResult.Resulting_Data_Centre_revenue = myCost.get_Scenario_HP_revenue();
		fullSimulationResult.Scenario_avoided_fuel_cost = myCost.get_Scenario_LP_revenue();

		fullSimulationResult.ESS_PCS_CAPEX = myCost.get_ESS_PCS_CAPEX();
		fullSimulationResult.ESS_PCS_OPEX = myCost.get_ESS_PCS_OPEX();
		fullSimulationResult.ESS_ENCLOSURE_CAPEX = myCost.get_ESS_ENCLOSURE_CAPEX();
		fullSimulationResult.ESS_ENCLOSURE_OPEX = myCost.get_ESS_ENCLOSURE_OPEX();
		fullSimulationResult.ESS_ENCLOSURE_DISPOSAL = myCost.get_ESS_ENCLOSURE_DISPOSAL();
		
		fullSimulationResult.PVpanel_CAPEX = myCost.get_PVpanel_CAPEX();
		fullSimulationResult.PVBoP_CAPEX = myCost.get_PVBoP_CAPEX();
		fullSimulationResult.PVroof_CAPEX = myCost.get_PVroof_CAPEX();
		fullSimulationResult.PVground_CAPEX = myCost.get_PVground_CAPEX();
		fullSimulationResult.PV_OPEX = myCost.get_PV_OPEX();
		
		fullSimulationResult.EV_CP_cost = myCost.get_EV_CP_cost();
		fullSimulationResult.EV_CP_install = myCost.get_EV_CP_install();

		fullSimulationResult.Grid_CAPEX = myCost.get_Grid_CAPEX();
		fullSimulationResult.ASHP_CAPEX = myCost.get_ASHP_CAPEX();

		float mEV_CP_cost;
		float mEV_CP_install;

		float mGrid_CAPEX;

		float mASHP_CAPEX;
	};

	


	fullSimulationResult.paramIndex = taskData.paramIndex;
	fullSimulationResult.total_annualised_cost = myCost.get_total_annualised_cost();
	fullSimulationResult.project_CAPEX = myCost.get_project_CAPEX();
	fullSimulationResult.scenario_cost_balance = myCost.get_scenario_cost_balance();
	fullSimulationResult.payback_horizon_years = myCost.get_payback_horizon_years();
	fullSimulationResult.scenario_carbon_balance = myCost.get_scenario_carbon_balance();

	
	//========================================

	/*WRITE DATA SECTION - AFTER PROFILING CLOCK STOPPED*/

	//End profiling

	// calculate elaspsed run time
	auto end = std::chrono::high_resolution_clock::now();
	std::chrono::duration<double> elapsed = end - start;
	float runtime = static_cast<float>(elapsed.count());

	fullSimulationResult.runtime = runtime;


	return fullSimulationResult;

}

SimulationResult Simulator::simulateScenario(const HistoricalData& historicalData, const TaskData& taskData, SimulationType simulationType) const {

	const FullSimulationResult& fullSimulationResult = simulateScenarioFull(historicalData, taskData, simulationType);
	SimulationResult simResult{};

	// By default we don't compute these sums during the main optimisation as we're only concerned with the output results
	// but for recall of specific scenarios (e.g. to write to a csv) we want to compute these
	if (simulationType == SimulationType::FullReporting) {
		simResult.Rgen_total = fullSimulationResult.Rgen_total.sum();
		simResult.Total_load = fullSimulationResult.Total_load.sum();
		simResult.ESUM = fullSimulationResult.ESUM.sum();
		simResult.ESS_available_discharge_power = fullSimulationResult.ESS_available_discharge_power.sum();
		simResult.ESS_available_charge_power = fullSimulationResult.ESS_available_charge_power.sum();
		simResult.ESS_Rgen_only_charge = fullSimulationResult.ESS_Rgen_only_charge.sum();
		simResult.ESS_discharge = fullSimulationResult.ESS_discharge.sum();
		simResult.ESS_charge = fullSimulationResult.ESS_charge.sum();
		simResult.ESS_resulting_SoC = fullSimulationResult.ESS_resulting_SoC.sum();
		simResult.Pre_grid_balance = fullSimulationResult.Pre_grid_balance.sum();
		simResult.Grid_Import = fullSimulationResult.Grid_Import.sum();
		simResult.Grid_Export = fullSimulationResult.Grid_Export.sum();
		simResult.Post_grid_balance = fullSimulationResult.Post_grid_balance.sum();
		simResult.Pre_flex_import_shortfall = fullSimulationResult.Pre_flex_import_shortfall.sum();
		simResult.Pre_Mop_curtailed_export = fullSimulationResult.Pre_Mop_curtailed_export.sum();
		simResult.Actual_import_shortfall = fullSimulationResult.Actual_import_shortfall.sum();
		simResult.Actual_curtailed_export = fullSimulationResult.Actual_curtailed_export.sum();
		simResult.Actual_high_priority_load = fullSimulationResult.Actual_high_priority_load.sum();
		simResult.Actual_low_priority_load = fullSimulationResult.Actual_low_priority_load.sum();
		simResult.Heatload = fullSimulationResult.Heatload.sum();
		simResult.Scaled_heatload = fullSimulationResult.Scaled_heatload.sum();
		simResult.Electrical_load_scaled_heat_yield = fullSimulationResult.Electrical_load_scaled_heat_yield.sum();
		simResult.Heat_shortfall = fullSimulationResult.Heat_shortfall.sum();
		simResult.Heat_surplus = fullSimulationResult.Heat_surplus.sum();
	}

	simResult.runtime = fullSimulationResult.runtime;
	simResult.paramIndex = fullSimulationResult.paramIndex;
	simResult.total_annualised_cost = fullSimulationResult.total_annualised_cost;
	simResult.project_CAPEX = fullSimulationResult.project_CAPEX;
	simResult.scenario_cost_balance = fullSimulationResult.scenario_cost_balance;
	simResult.payback_horizon_years = fullSimulationResult.payback_horizon_years;
	simResult.scenario_carbon_balance = fullSimulationResult.scenario_carbon_balance;

	return simResult;
}


year_TS Simulator::calculateRGenTotal(const HistoricalData& historicalData, const TaskData& taskData) const {
	year_TS RGen1 = historicalData.RGen_data_1 * taskData.ScalarRG1;
	year_TS RGen2 = historicalData.RGen_data_2 * taskData.ScalarRG2;
	year_TS RGen3 = historicalData.RGen_data_3 * taskData.ScalarRG3;
	year_TS RGen4 = historicalData.RGen_data_4 * taskData.ScalarRG4;

	return RGen1 + RGen2 + RGen3 + RGen4;
}

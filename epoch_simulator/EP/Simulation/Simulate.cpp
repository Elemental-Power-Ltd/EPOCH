#include "Simulate.hpp"

#include <chrono>
#include <iostream>
#include <Eigen/Core>

#include "Assets.h"
#include "Config.h"
#include "Eload.h"
#include "Grid.h"
#include "Hload.h"
#include "Costs.h"

Simulator::Simulator() {

}


FullSimulationResult Simulator::simulateScenario(const HistoricalData& historicalData, const Config& myConfig) const {
	/*CALCULATIVE SECTION - START PROFILING */
	auto start = std::chrono::high_resolution_clock::now(); //start runtime clock

	Eload MountEload{historicalData, myConfig};
	year_TS RGen_total = calculateRGenTotal(historicalData, myConfig);
	// Final ESUM (electrical acitivity) is Total load minus Rgen
	year_TS ESUM = MountEload.getTS_Total_load() - RGen_total;

	ESS MountBESS{ myConfig };
	MountBESS.initialise(ESUM[0]);
	MountBESS.runTimesteps(ESUM);

	Grid MountGrid{ myConfig };
	MountGrid.performGridCalculations(ESUM, MountBESS);

	Hload MountHload{ historicalData, myConfig };
	MountHload.performHeatCalculations(historicalData, myConfig, MountGrid);

	//Data reporting
	Eigen::VectorXf Total_load_vect = MountEload.getTS_Total_load();

	Eigen::VectorXf ESS_available_discharge_power_vect = MountBESS.getTS_ESS_available_discharge_power();
	Eigen::VectorXf ESS_available_charge_power_vect = MountBESS.getTS_ESS_available_charge_power();
	Eigen::VectorXf TS_ESS_Rgen_only_charge_vect = MountBESS.getTS_ESS_Rgen_only_charge();
	Eigen::VectorXf TS_ESS_discharge_vect = MountBESS.getTS_ESS_discharge();
	Eigen::VectorXf TS_ESS_charge_vect = MountBESS.getTS_ESS_charge();
	Eigen::VectorXf TS_ESS_resulting_SoC_vect = MountBESS.getTS_ESS_resulting_SoC();
	Eigen::VectorXf TS_Pre_grid_balance_vect = MountGrid.getTS_Pre_grid_balance();
	Eigen::VectorXf TS_Grid_Import_vect = MountGrid.getTS_GridImport();
	Eigen::VectorXf TS_Grid_Export_vect = MountGrid.getTS_GridExport();
	Eigen::VectorXf TS_Post_grid_balance_vect = MountGrid.getTS_Post_grid_balance();
	Eigen::VectorXf TS_Pre_flex_import_shortfall_vect = MountGrid.getTS_Pre_flex_import_shortfall();
	Eigen::VectorXf TS_Pre_Mop_curtailed_export_vect = MountGrid.getTS_Pre_Mop_curtailed_Export();
	Eigen::VectorXf TS_Actual_import_shortfall_vect = MountGrid.getTS_Actual_import_shortfall();
	Eigen::VectorXf TS_Actual_curtailed_export_vect = MountGrid.getTS_Actual_curtailed_export();
	Eigen::VectorXf TS_Actual_high_priority_load_vect = MountGrid.getActualHighPriorityLoad();
	Eigen::VectorXf TS_Actual_low_priority_load_vect = MountGrid.getActualLowPriorityLoad();
	Eigen::VectorXf scaled_heatload_vect = MountHload.getTS_Heatload();
	Eigen::VectorXf Electrical_load_scaled_heat_yield_vect = MountHload.getTS_Electrical_load_scaled_heat_yield();
	Eigen::VectorXf TS_Heat_shortfall_vect = MountHload.getTS_Heat_shortfall();
	Eigen::VectorXf TS_Heat_surplus_vect = MountHload.getTS_Heat_surplus();

	Costs myCost(myConfig);
	myCost.calculateCosts(MountEload, MountHload, MountGrid);


	//========================================

	/*WRITE DATA SECTION - AFTER PROFILING CLOCK STOPPED*/

	//End profiling

	// calculate elaspsed run time
	auto end = std::chrono::high_resolution_clock::now();
	std::chrono::duration<double> elapsed = end - start;
	float runtime = static_cast<float>(elapsed.count());

	std::cout << "Runtime: " << elapsed.count() << " seconds" << '\n'; // print elapsed run time

	FullSimulationResult fullSimulationResult;

	fullSimulationResult.Rgen_total = RGen_total;
	fullSimulationResult.Total_load = Total_load_vect;
	fullSimulationResult.ESUM = ESUM;
	fullSimulationResult.ESS_available_discharge_power = ESS_available_discharge_power_vect;
	fullSimulationResult.ESS_available_charge_power = ESS_available_charge_power_vect;
	fullSimulationResult.ESS_Rgen_only_charge = TS_ESS_Rgen_only_charge_vect;
	fullSimulationResult.ESS_discharge = TS_ESS_discharge_vect;
	fullSimulationResult.ESS_charge = TS_ESS_charge_vect;
	fullSimulationResult.ESS_resulting_SoC = TS_ESS_resulting_SoC_vect;
	fullSimulationResult.Pre_grid_balance = TS_Pre_grid_balance_vect;
	fullSimulationResult.Grid_Import = TS_Grid_Import_vect;
	fullSimulationResult.Grid_Export = TS_Grid_Export_vect;
	fullSimulationResult.Post_grid_balance = TS_Post_grid_balance_vect;
	fullSimulationResult.Pre_flex_import_shortfall = TS_Pre_flex_import_shortfall_vect;
	fullSimulationResult.Pre_Mop_curtailed_export = TS_Pre_Mop_curtailed_export_vect;
	fullSimulationResult.Actual_import_shortfall = TS_Actual_import_shortfall_vect;
	fullSimulationResult.Actual_curtailed_export = TS_Actual_curtailed_export_vect;
	fullSimulationResult.Actual_high_priority_load = TS_Actual_high_priority_load_vect;
	fullSimulationResult.Actual_low_priority_load = TS_Actual_low_priority_load_vect;
	fullSimulationResult.heatload = historicalData.heatload_data;
	fullSimulationResult.scaled_heatload = scaled_heatload_vect;
	fullSimulationResult.Electrical_load_scaled_heat_yield = Electrical_load_scaled_heat_yield_vect;
	fullSimulationResult.Heat_shortfall = TS_Heat_shortfall_vect;
	fullSimulationResult.Heat_surplus = TS_Heat_surplus_vect;

	fullSimulationResult.runtime = runtime;
	fullSimulationResult.paramIndex = myConfig.getParamIndex();
	fullSimulationResult.total_annualised_cost = myCost.get_total_annualised_cost();
	fullSimulationResult.project_CAPEX = myCost.get_project_CAPEX();
	fullSimulationResult.scenario_cost_balance = myCost.get_scenario_cost_balance();
	fullSimulationResult.payback_horizon_years = myCost.get_payback_horizon_years();
	fullSimulationResult.scenario_carbon_balance = myCost.get_scenario_carbon_balance();

	return fullSimulationResult;

}

SimulationResult Simulator::simulateScenarioAndSum(const HistoricalData& historicalData, const Config& config, bool computeAllSums) const {
	const FullSimulationResult& fullSimulationResult = simulateScenario(historicalData, config);

	SimulationResult simResult{};

	// By default we don't compute these sums during the main optimisation as we're only concerned with the output results
	// but for recall of specific scenarios (e.g. to write to a csv) we want to compute these
	if (computeAllSums) {
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
		simResult.heatload = fullSimulationResult.heatload.sum();
		simResult.scaled_heatload = fullSimulationResult.scaled_heatload.sum();
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


year_TS Simulator::calculateRGenTotal(const HistoricalData& historicalData, const Config& config) const {
	year_TS RGen1 = historicalData.RGen_data_1 * config.getScalarRG1();
	year_TS RGen2 = historicalData.RGen_data_2 * config.getScalarRG2();
	year_TS RGen3 = historicalData.RGen_data_3 * config.getScalarRG3();
	year_TS RGen4 = historicalData.RGen_data_4 * config.getScalarRG4();

	return RGen1 + RGen2 + RGen3 + RGen4;
}

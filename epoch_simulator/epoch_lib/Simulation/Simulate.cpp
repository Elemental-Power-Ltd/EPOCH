#include "Simulate.hpp"

#include <chrono>
#include <iostream>
#include <Eigen/Core>

#include "TaskData.hpp"
#include "../Definitions.hpp"

#include "Assets.hpp"
#include "Eload.hpp"
#include "Grid.hpp"
#include "Hload.hpp"
#include "Costs.hpp"

#include "Config.hpp"	//AS ADD
#include "TempSum.hpp"	//AS ADD

#include "Hotel.hpp"	//AS ADD
#include "PV.hpp"		//AS ADD
#include "EV.hpp"		//AS ADD
#include "Grid3.hpp"	//AS ADD
#include "MOP.hpp"		//AS ADD
#include "GasCH.hpp"	//AS ADD
#include "Battery.hpp"	//AS ADD
#include "ESS.hpp"		//AS ADD
#include "ASHPperf.hpp"	//AS ADD
#include "ASHP.hpp"		//AS ADD
#include "DataC.hpp"	//AS ADD

Simulator::Simulator() {

}

FullSimulationResult Simulator::simulateScenarioFull(const HistoricalData& historicalData, const TaskData& taskData, SimulationType simulationType) const {
	/*CALCULATIVE SECTION - START PROFILING */
	auto start = std::chrono::high_resolution_clock::now(); //start runtime clock

	// MOVE COST CALCS here (exit if CAPEX exceeded, set results to sensible values?)

	/* INITIALISE classes that support energy sums and object precedence */
	Config_cl Config(taskData);	// flags energy component presence in TaskData & balancing modes
	TempSum_cl TempSum();		// class of arrays for running totals (replace ESUM and Heat)
	
	// INITIALISE Energy Components
	Hotel_cl Hotel(historicalData, taskData);
	PVbasic_cl PV1(historicalData, taskData);
	EVbasic_cl EV1(historicalData, taskData);

		// SLB hot water cyclinder
	// HotWcylA_cl HotWaterCyl(historicalData, taskData);

	Battery_cl ESSbattery(taskData);
	
	// init ESS object (0= None, 1=basic, 2=hybrid)
	ESSbasic_cl ESSmain(taskData, ESSbattery);

	// ASHPperf & ASHPhot better inside the ESS class/object
	ASHPData_st ASHPData1;
	ASHPData1.TScount = taskData.calculate_timesteps();
	ASHPData1.PowerScalar = taskData.timestep_hours;
	ASHPData1.HeatMode = taskData.ASHP_RadTemp;      // Output water (radiator) temp.
	ASHPData1.HotTemp = taskData.ASHP_HotTemp;       // Hotroom (DataC waste heat) air temp.;
	ASHPperf_cl ASHPperf1(historicalData, ASHPData1);
	ASHPhot_cl ASHP1(historicalData, taskData, ASHPData1, ASHPperf1);	// Use pointer to ASHPperf1

	DataC_ASHP_cl DataC(historicalData, taskData, ASHP1);

	// REMOVE THE 3 FROM GRID WHEN CLEANING OLD CODE
	Grid_cl Grid3(historicalData, taskData);
	MOP_cl MOP(taskData);
	GasCH_cl GasCH(taskData);

	// OLD CODE

	year_TS RGen_total = calculateRGenTotal(historicalData, taskData);

	Hload MountHload(historicalData, taskData); // initialise Hload based on historical data and taskdata
	Grid MountGrid(taskData); //initialise Grid based on taskdata

	MountHload.performHeatCalculations(historicalData, taskData);
	
	Eload MountEload(historicalData, taskData); // initialise Eload based on historical data and taskdata

	ESS MountBESS(taskData); //initialise ESS based on taskdata

	MountEload.calculateLoads(MountHload, MountBESS, RGen_total, taskData);
	
	year_TS ESUM = MountEload.getTotal_target_load_fixed_flex() - RGen_total;

	MountBESS.initialise(ESUM[0]);
	MountBESS.runTimesteps(ESUM);

	MountGrid.performGridCalculations(ESUM, MountBESS, MountHload, MountEload.getHeadroomL1());

	MountEload.calculateElectricHeat(MountGrid, MountHload, taskData);

	MountHload.calculateHeatSUM(MountEload.getData_Centre_HP_load_scalar(), MountGrid.getActualLowPriorityLoad());

	Costs myCost(taskData);
	myCost.calculateCosts(MountEload, MountHload, MountGrid, MountBESS);

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
		fullSimulationResult.Scaled_heatload = MountHload.getHeatload();
		fullSimulationResult.Electrical_load_scaled_heat_yield = MountHload.getElectricalLoadScaledHeatYield();
		fullSimulationResult.Heat_shortfall = MountHload.getHeatShortfall();
		fullSimulationResult.Heat_surplus = MountHload.getEHeatSurplus();
	}


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

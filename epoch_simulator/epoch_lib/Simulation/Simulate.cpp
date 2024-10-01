#include "Simulate.hpp"

#include <chrono>
#include <iostream>
#include <limits> 
#include <memory>

#include <Eigen/Core>

#include "TaskData.hpp"
#include "../Definitions.hpp"

#include "Costs.hpp"
#include "HotWaterCylinder.hpp"

#include "Config.hpp"
#include "TempSum.hpp"

#include "Hotel.hpp"
#include "PV.hpp"
#include "EV.hpp"
#include "Grid.hpp"
#include "MOP.hpp"
#include "GasCH.hpp"
#include "Battery.hpp"
#include "ESS.hpp"
#include "ASHPperf.hpp"
#include "ASHP.hpp"
#include "HeatPumpController.hpp"

#include "Components/DataCentre.hpp"

Simulator::Simulator() {

}

FullSimulationResult Simulator::simulateScenarioFull(const HistoricalData& historicalData, const TaskData& taskData, SimulationType simulationType) const {
	/*CALCULATIVE SECTION - START PROFILING */
	auto start = std::chrono::high_resolution_clock::now(); //start runtime clock

	// Calculate CAPEX upfront to discard scenarios above CAPEX contraint early 
	Costs myCost(historicalData, taskData);
	myCost.calculate_Project_CAPEX();
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

	/* INITIALISE classes that support energy sums and object precedence */
	Config config(taskData);	// flags energy component presence in TaskData & balancing modes
	TempSum tempSum(taskData);		// class of arrays for running totals (replace ESUM and Heat)
	
	// INITIALISE Energy Components
	Hotel hotel(historicalData, taskData);
	BasicPV PV1(historicalData, taskData);
	BasicElectricVehicle EV1(historicalData, taskData);
	
	// init ESS object (0= None, 1=basic, 2=hybrid)
	BasicESS ESSmain(taskData);

	std::unique_ptr<DataCentre> dataCentre;
	std::unique_ptr<AmbientHeatPumpController> ambientController;

	if (config.DataC() == 1 && taskData.ASHP_HSource == 2) {
		// make a DataCentre with a hotroom heatpump
		dataCentre = std::make_unique<DataCentreWithASHP>(historicalData, taskData);
	}
	else if (config.DataC() == 1 && taskData.ASHP_HSource == 1) {
		// make a basic data centre (without a heatpump)
		dataCentre =  std::make_unique<BasicDataCentre>(historicalData, taskData);
		ambientController = std::make_unique<AmbientHeatPumpController>(historicalData, taskData);
	}
	else if (config.DataC() != 1 && taskData.ASHP_HSource == 1) {
		// no DataCentre, ambient heatpump
		ambientController = std::make_unique<AmbientHeatPumpController>(historicalData, taskData);
	}
	else {
		// INVALID STATE
		throw std::exception();
	}


	// REMOVE THE 3 FROM GRID WHEN CLEANING OLD CODE
	Grid grid(historicalData, taskData);
	MOP MOP(taskData);
	GasCombustionHeater GasCH(taskData);
	
	HotWaterCylinder hotWaterCylinder{ historicalData, taskData };

	// NON-BALANCING LOGIC

	hotel.AllCalcs(tempSum);
	PV1.AllCalcs(tempSum);


	if (config.EV1bal() == 1) {
		EV1.AllCalcs(tempSum);
	}

	// TODO - consider applying battery aux load before considering DHW
	// something like: ESSmain.ApplyAuxLoad(tempSum);

	hotWaterCylinder.AllCalcs(tempSum);

	if (taskData.ASHP_HSource == 1) {
		ambientController->AllCalcs(tempSum);
	}

	if (config.DataCbal() == 1) {
		dataCentre->AllCalcs(tempSum);
	} 

	// BALANCING LOOP

	float futureEnergy = 0.0f;
	int timesteps = taskData.calculate_timesteps();

	if (config.DataCbal() == 2 && config.EV1bal() == 2) {
		// This represents the logic in M-VEST v0-7:
		// EV is curtailed before the Data Centre

		for (int t = 0; t < timesteps; t++) {
			futureEnergy = grid.AvailImport() + ESSmain.AvailDisch() - dataCentre->getTargetLoad(t);
			EV1.StepCalc(tempSum, futureEnergy, t);
			futureEnergy = grid.AvailImport() + ESSmain.AvailDisch();
			dataCentre->StepCalc(tempSum, futureEnergy, t);
			ESSmain.StepCalc(tempSum, grid.AvailImport(), t);
		}
	}
	else if (config.DataCbal() == 1 && config.EV1bal() == 2) {
		for (int t = 0; t < timesteps; t++) {
			futureEnergy = grid.AvailImport() + ESSmain.AvailDisch();
			EV1.StepCalc(tempSum, futureEnergy, t);
			ESSmain.StepCalc(tempSum, grid.AvailImport(), t);
		}
	}
	else if (config.DataCbal() == 2 && config.EV1bal() == 1) {
		for (int t = 0; t < timesteps; t++) {
			futureEnergy = grid.AvailImport() + ESSmain.AvailDisch();
			dataCentre->StepCalc(tempSum, futureEnergy, t);
			ESSmain.StepCalc(tempSum, grid.AvailImport(), t);
		}
	}
	else {
		for (int t = 0; t < timesteps; t++) {
			ESSmain.StepCalc(tempSum, grid.AvailImport(), t);
		}
	}

	MOP.AllCalcs(tempSum);
	grid.AllCalcs(tempSum);
	GasCH.AllCalcs(tempSum);

	FullSimulationResult fullSimulationResult;

	tempSum.Report(fullSimulationResult);
	hotel.Report(fullSimulationResult);
	PV1.Report(fullSimulationResult);
	EV1.Report(fullSimulationResult);
	ESSmain.Report(fullSimulationResult);
	dataCentre->Report(fullSimulationResult);
	grid.Report(fullSimulationResult);
	MOP.Report(fullSimulationResult);
	GasCH.Report(fullSimulationResult);
	hotWaterCylinder.Report(fullSimulationResult);

	CostVectors costVectors;

	costVectors.actual_ev_load_e = fullSimulationResult.EV_actualload;
	costVectors.actual_data_centre_load_e = fullSimulationResult.Data_centre_actual_load;
	costVectors.building_load_e = fullSimulationResult.Hotel_load;
	costVectors.heatload_h = fullSimulationResult.Heatload;
	costVectors.heat_shortfall_h = fullSimulationResult.Heat_shortfall;
	costVectors.grid_import_e = fullSimulationResult.Grid_Import;
	costVectors.grid_export_e = fullSimulationResult.Grid_Export;
	costVectors.actual_low_priority_load_e = fullSimulationResult.MOP_load;


	myCost.calculateCosts_no_CAPEX(costVectors);

	//Data reporting

	if (simulationType == SimulationType::FullReporting) {
		//fullSimulationResult.Baseline_electricity_cost = myCost.get_Baseline_elec_cost();
		//fullSimulationResult.Baseline_fuel_cost = myCost.get_Baseline_fuel_cost();

		//fullSimulationResult.Baseline_electricity_carbon = myCost.get_Baseline_elec_CO2e();
		//fullSimulationResult.Baseline_fuel_carbon = myCost.get_Baseline_fuel_CO2e();

		//fullSimulationResult.Scenario_electricity_cost = myCost.get_Scenario_import_cost();
		//fullSimulationResult.Scenario_fuel_cost = myCost.get_Scenario_fuel_cost();
		//fullSimulationResult.Scenario_grid_export_cost = myCost.get_Scenario_export_cost();
		//
		//fullSimulationResult.Scenario_electricity_carbon = myCost.get_Scenario_elec_CO2e();
		//fullSimulationResult.Scenario_fuel_carbon = myCost.get_Scenario_fuel_CO2e();
		//fullSimulationResult.Scenario_grid_export_carbon = myCost.get_Scenario_export_CO2e();
		//fullSimulationResult.Scenario_avoided_fuel_carbon = myCost.get_Scenario_LP_CO2e();

		//fullSimulationResult.Resulting_EV_charge_revenue = myCost.get_Scenario_EV_revenue();
		//fullSimulationResult.Resulting_Data_Centre_revenue = myCost.get_Scenario_HP_revenue();
		//fullSimulationResult.Scenario_avoided_fuel_cost = myCost.get_Scenario_LP_revenue();

		//fullSimulationResult.ESS_PCS_CAPEX = myCost.get_ESS_PCS_CAPEX();
		//fullSimulationResult.ESS_PCS_OPEX = myCost.get_ESS_PCS_OPEX();
		//fullSimulationResult.ESS_ENCLOSURE_CAPEX = myCost.get_ESS_ENCLOSURE_CAPEX();
		//fullSimulationResult.ESS_ENCLOSURE_OPEX = myCost.get_ESS_ENCLOSURE_OPEX();
		//fullSimulationResult.ESS_ENCLOSURE_DISPOSAL = myCost.get_ESS_ENCLOSURE_DISPOSAL();
		//
		//fullSimulationResult.PVpanel_CAPEX = myCost.get_PVpanel_CAPEX();
		//fullSimulationResult.PVBoP_CAPEX = myCost.get_PVBoP_CAPEX();
		//fullSimulationResult.PVroof_CAPEX = myCost.get_PVroof_CAPEX();
		//fullSimulationResult.PVground_CAPEX = myCost.get_PVground_CAPEX();
		//fullSimulationResult.PV_OPEX = myCost.get_PV_OPEX();
		//
		//fullSimulationResult.EV_CP_cost = myCost.get_EV_CP_cost();
		//fullSimulationResult.EV_CP_install = myCost.get_EV_CP_install();

		//fullSimulationResult.Grid_CAPEX = myCost.get_Grid_CAPEX();
		//fullSimulationResult.ASHP_CAPEX = myCost.get_ASHP_CAPEX();

		//float mEV_CP_cost;
		//float mEV_CP_install;

		//float mGrid_CAPEX;

		//float mASHP_CAPEX;
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

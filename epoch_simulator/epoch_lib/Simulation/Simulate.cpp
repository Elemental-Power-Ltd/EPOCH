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
#include "ASHP.hpp"
#include "HeatPumpController.hpp"

#include "Components/DataCentre.hpp"

Simulator::Simulator() {

}

SimulationResult Simulator::simulateScenario(const HistoricalData& historicalData, const TaskData& taskData, SimulationType simulationType) const {
	/*CALCULATIVE SECTION - START PROFILING */
	auto start = std::chrono::high_resolution_clock::now(); //start runtime clock

	// Calculate CAPEX upfront to discard scenarios above CAPEX contraint early 
	Costs myCost(historicalData, taskData);
	myCost.calculate_Project_CAPEX();
	if (taskData.CAPEX_limit*1000 < myCost.get_project_CAPEX())
	{
		auto simulationResult = makeInvalidResult(taskData);

		// but this invalid result can still have a valid CAPEX
		simulationResult.project_CAPEX = myCost.get_project_CAPEX();
		return simulationResult;
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

	if (config.dataCentrePresent() && taskData.ASHP_HSource == 2) {
		// make a DataCentre with a hotroom heatpump
		dataCentre = std::make_unique<DataCentreWithASHP>(historicalData, taskData);
	}
	else if (config.dataCentrePresent() && taskData.ASHP_HSource == 1) {
		// make a basic data centre (without a heatpump)
		dataCentre =  std::make_unique<BasicDataCentre>(historicalData, taskData);
		ambientController = std::make_unique<AmbientHeatPumpController>(historicalData, taskData);
	}
	else if (!config.dataCentrePresent() && taskData.ASHP_HSource == 1) {
		// no DataCentre, ambient heatpump
		ambientController = std::make_unique<AmbientHeatPumpController>(historicalData, taskData);
	}
	else {
		// WARNING - THIS IS AN INVALID STATE

		// return an 'invalid' simulation result
		return makeInvalidResult(taskData);
	}


	// REMOVE THE 3 FROM GRID WHEN CLEANING OLD CODE
	Grid grid(historicalData, taskData);
	MOP MOP(taskData);
	GasCombustionHeater GasCH(taskData);
	
	HotWaterCylinder hotWaterCylinder{ historicalData, taskData };

	// NON-BALANCING LOGIC

	hotel.AllCalcs(tempSum);
	PV1.AllCalcs(tempSum);


	if (config.getEVFlag() == EVFlag::NON_BALANCING) {
		EV1.AllCalcs(tempSum);
	}

	// TODO - consider applying battery aux load before considering DHW
	// something like: ESSmain.ApplyAuxLoad(tempSum);

	hotWaterCylinder.AllCalcs(tempSum);

	if (taskData.ASHP_HSource == 1) {
		ambientController->AllCalcs(tempSum);
	}

	if (config.getDataCentreFlag() == DataCentreFlag::NON_BALANCING) {
		dataCentre->AllCalcs(tempSum);
	} 

	// BALANCING LOOP

	float futureEnergy = 0.0f;
	int timesteps = taskData.calculate_timesteps();

	auto dcFlag = config.getDataCentreFlag();
	auto evFlag = config.getEVFlag();

	if (dcFlag == DataCentreFlag::BALANCING && evFlag == EVFlag::BALANCING) {
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
	else if (dcFlag != DataCentreFlag::BALANCING && evFlag == EVFlag::BALANCING) {
		for (int t = 0; t < timesteps; t++) {
			futureEnergy = grid.AvailImport() + ESSmain.AvailDisch();
			EV1.StepCalc(tempSum, futureEnergy, t);
			ESSmain.StepCalc(tempSum, grid.AvailImport(), t);
		}
	}
	else if (dcFlag == DataCentreFlag::BALANCING && evFlag != EVFlag::BALANCING) {
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

	SimulationResult result;

	result.report_data = ReportData();
	ReportData& reportData = *result.report_data;

	tempSum.Report(reportData);
	hotel.Report(reportData);
	PV1.Report(reportData);
	EV1.Report(reportData);
	ESSmain.Report(reportData);
	if (config.dataCentrePresent()) {
		dataCentre->Report(reportData);
	}
	else {
		ambientController->Report(reportData);
	}
	// TODO do HeatPump Reporting
	grid.Report(reportData);
	MOP.Report(reportData);
	GasCH.Report(reportData);
	hotWaterCylinder.Report(reportData);

	CostVectors costVectors;

	costVectors.actual_ev_load_e = reportData.EV_actualload;
	costVectors.actual_data_centre_load_e = reportData.Data_centre_actual_load;
	costVectors.building_load_e = reportData.Hotel_load;
	costVectors.heatload_h = reportData.Heatload;
	costVectors.heat_shortfall_h = reportData.Heat_shortfall;
	costVectors.grid_import_e = reportData.Grid_Import;
	costVectors.grid_export_e = reportData.Grid_Export;
	costVectors.actual_low_priority_load_e = reportData.MOP_load;


	myCost.calculateCosts_no_CAPEX(costVectors);

	//Data reporting

	if (simulationType == SimulationType::FullReporting) {
		//reportData.Baseline_electricity_cost = myCost.get_Baseline_elec_cost();
		//reportData.Baseline_fuel_cost = myCost.get_Baseline_fuel_cost();

		//reportData.Baseline_electricity_carbon = myCost.get_Baseline_elec_CO2e();
		//reportData.Baseline_fuel_carbon = myCost.get_Baseline_fuel_CO2e();

		//reportData.Scenario_electricity_cost = myCost.get_Scenario_import_cost();
		//reportData.Scenario_fuel_cost = myCost.get_Scenario_fuel_cost();
		//reportData.Scenario_grid_export_cost = myCost.get_Scenario_export_cost();
		//
		//reportData.Scenario_electricity_carbon = myCost.get_Scenario_elec_CO2e();
		//reportData.Scenario_fuel_carbon = myCost.get_Scenario_fuel_CO2e();
		//reportData.Scenario_grid_export_carbon = myCost.get_Scenario_export_CO2e();
		//reportData.Scenario_avoided_fuel_carbon = myCost.get_Scenario_LP_CO2e();

		//reportData.Resulting_EV_charge_revenue = myCost.get_Scenario_EV_revenue();
		//reportData.Resulting_Data_Centre_revenue = myCost.get_Scenario_HP_revenue();
		//reportData.Scenario_avoided_fuel_cost = myCost.get_Scenario_LP_revenue();

		//reportData.ESS_PCS_CAPEX = myCost.get_ESS_PCS_CAPEX();
		//reportData.ESS_PCS_OPEX = myCost.get_ESS_PCS_OPEX();
		//reportData.ESS_ENCLOSURE_CAPEX = myCost.get_ESS_ENCLOSURE_CAPEX();
		//reportData.ESS_ENCLOSURE_OPEX = myCost.get_ESS_ENCLOSURE_OPEX();
		//reportData.ESS_ENCLOSURE_DISPOSAL = myCost.get_ESS_ENCLOSURE_DISPOSAL();
		//
		//reportData.PVpanel_CAPEX = myCost.get_PVpanel_CAPEX();
		//reportData.PVBoP_CAPEX = myCost.get_PVBoP_CAPEX();
		//reportData.PVroof_CAPEX = myCost.get_PVroof_CAPEX();
		//reportData.PVground_CAPEX = myCost.get_PVground_CAPEX();
		//reportData.PV_OPEX = myCost.get_PV_OPEX();
		//
		//reportData.EV_CP_cost = myCost.get_EV_CP_cost();
		//reportData.EV_CP_install = myCost.get_EV_CP_install();

		//reportData.Grid_CAPEX = myCost.get_Grid_CAPEX();
		//reportData.ASHP_CAPEX = myCost.get_ASHP_CAPEX();

		//float mEV_CP_cost;
		//float mEV_CP_install;

		//float mGrid_CAPEX;

		//float mASHP_CAPEX;
	};

	
	result.paramIndex = taskData.paramIndex;
	result.total_annualised_cost = myCost.get_total_annualised_cost();
	result.project_CAPEX = myCost.get_project_CAPEX();
	result.scenario_cost_balance = myCost.get_scenario_cost_balance();
	result.payback_horizon_years = myCost.get_payback_horizon_years();
	result.scenario_carbon_balance = myCost.get_scenario_carbon_balance();

	
	//========================================

	/*WRITE DATA SECTION - AFTER PROFILING CLOCK STOPPED*/

	//End profiling

	// calculate elaspsed run time
	auto end = std::chrono::high_resolution_clock::now();
	std::chrono::duration<double> elapsed = end - start;
	float runtime = static_cast<float>(elapsed.count());

	result.runtime = runtime;


	return result;

}

SimulationResult Simulator::makeInvalidResult(const TaskData& taskData) const {
	// When a scenario is invalid, for now we return the FLT_MAX or FLT_MIN for each objective as appropriate

	// TODO - apply proper fix for 'nullable' results
	SimulationResult fullSimulationResult;
	fullSimulationResult.paramIndex = taskData.paramIndex;

	fullSimulationResult.project_CAPEX = std::numeric_limits<float>::max();
	fullSimulationResult.total_annualised_cost = std::numeric_limits<float>::max();
	fullSimulationResult.scenario_cost_balance = std::numeric_limits<float>::lowest();
	fullSimulationResult.payback_horizon_years = std::numeric_limits<float>::max();
	fullSimulationResult.scenario_carbon_balance = std::numeric_limits<float>::lowest();

	return fullSimulationResult;
}


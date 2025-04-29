#include "Simulate.hpp"

#include <chrono>
#include <format>
#include <iostream>
#include <limits> 
#include <memory>
#include <stdexcept>

#include <Eigen/Core>
#include <spdlog/spdlog.h>

#include "TaskData.hpp"
#include "../Definitions.hpp"

#include "Costs/Usage.hpp"
#include "Costs/Compare.hpp"
#include "DayTariffStats.hpp"
#include "HotWaterCylinder.hpp"

#include "Config.hpp"
#include "TempSum.hpp"

#include "Hotel.hpp"
#include "PV.hpp"
#include "EV.hpp"
#include "Grid.hpp"
#include "Mop.hpp"
#include "GasCH.hpp"
#include "ASHP.hpp"
#include "HeatPumpController.hpp"

#include "Components/DataCentre.hpp"
#include "Components/ESS/ESS.hpp"

Simulator::Simulator(SiteData siteData):
	mSiteData(siteData)
{

	TaskData baselineTaskData{};
	baselineTaskData.building = Building();
	baselineTaskData.grid = GridData();
	baselineTaskData.gas_heater = GasCHData();

	// we construct a TaskData with oversized grid and gas capacities
	// to ensure there is no shortfall
	baselineTaskData.grid->grid_import = 1000000.0f;
	baselineTaskData.grid->grid_export = 1000000.0f;
	baselineTaskData.gas_heater->maximum_output = 1000000.0f;

	auto baselineReportData = simulateTimesteps(baselineTaskData);
	CostVectors baselineCostVectors = extractCostVectors(baselineReportData, baselineTaskData);
	mBaselineUsage = calculateUsage(mSiteData, baselineTaskData, baselineCostVectors);

}

SimulationResult Simulator::simulateScenario(const TaskData& taskData, SimulationType simulationType) const {

	auto start = std::chrono::high_resolution_clock::now();

	try {
		validateScenario(taskData);
	}
	catch (const std::runtime_error& e) {
		spdlog::warn("Invalid scenario: {}", e.what());
		return makeInvalidResult(taskData);
	}

	// Calculate CAPEX upfront to discard scenarios above CAPEX contraint early 
	const CapexBreakdown capex = calculateCapex(taskData);

	if (taskData.config.capex_limit < capex.total_capex) {
		auto simulationResult = makeInvalidResult(taskData);

		// but this invalid result can still have a valid CAPEX
		simulationResult.project_CAPEX = capex.total_capex;
		return simulationResult;
	}

	SimulationResult result{};

	result.report_data = simulateTimesteps(taskData, simulationType);

	const CostVectors& costVectors = extractCostVectors(result.report_data.value(), taskData);

	auto scenarioUsage = calculateUsage(mSiteData, taskData, costVectors);

	auto comparison = compareScenarios(mBaselineUsage, scenarioUsage);

	result.project_CAPEX = scenarioUsage.capex_breakdown.total_capex;
	result.total_annualised_cost = comparison.total_annualised_cost;
	result.scenario_cost_balance = comparison.cost_balance;
	result.payback_horizon_years = comparison.payback_horizon_years;
	result.scenario_carbon_balance_scope_1 = comparison.carbon_balance_scope_1;
	result.scenario_carbon_balance_scope_2 = comparison.carbon_balance_scope_2;

	result.metrics.total_gas_used = result.report_data->GasCH_load.sum();
	result.metrics.total_electricity_imported = result.report_data->Grid_Import.sum();
	result.metrics.total_electricity_generated = result.report_data->PVacGen.sum();
	result.metrics.total_electricity_exported = result.report_data->Grid_Export.sum();

	result.metrics.total_electrical_shortfall = result.report_data->Actual_import_shortfall.sum();
	result.metrics.total_heat_shortfall = result.report_data->Heat_shortfall.sum();

	result.metrics.total_gas_import_cost = scenarioUsage.fuel_cost;
	result.metrics.total_electricity_import_cost = scenarioUsage.elec_cost;
	result.metrics.total_electricity_export_gain = scenarioUsage.export_revenue;

	if (simulationType != SimulationType::FullReporting) {
		// TEMPORARY HACK
		// until the costs have been refactored, we are always doing full reporting
		// this is a lazy way of getting the vectors we need into costVectors

		// in order to preserve the correct appearance of there being no reportData,
		// we remove the reportData again here
		result.report_data = std::nullopt;
	}
	
	// calculate elaspsed run time
	auto end = std::chrono::high_resolution_clock::now();
	std::chrono::duration<double> elapsed = end - start;
	float runtime = static_cast<float>(elapsed.count());

	result.runtime = runtime;

	return result;
}

void Simulator::validateScenario(const TaskData& taskData) const {
	// check fabric_intervention_index is in bounds
	if (taskData.building) {
		// building_hload is considered index 0 so we are effectively 1-based indexing
		if (taskData.building->fabric_intervention_index >= mSiteData.fabric_interventions.size() + 1) {
			throw std::runtime_error(std::format(
				"Cannot use fabric_intervention_index of {} with {} fabric interventions",
				taskData.building->fabric_intervention_index, mSiteData.fabric_interventions.size()
			));
		}
	}

	// check tariff_index is in bounds
	if (taskData.grid) {
		if (taskData.grid->tariff_index >= mSiteData.import_tariffs.size()) {
			throw std::runtime_error(std::format(
				"Cannot use tariff_index of {} with {} tariffs provided",
				taskData.grid->tariff_index, mSiteData.import_tariffs.size()
			));
		}
	}

	// check yield_scalars and solar_yields match
	if (taskData.renewables) {
		if (taskData.renewables->yield_scalars.size() > mSiteData.solar_yields.size()) {
			throw std::runtime_error(std::format(
				"Mismatch: TaskData supplied {} yield_scalars but SiteData only supplied {} solar_yields",
				taskData.renewables->yield_scalars.size(), mSiteData.solar_yields.size()
			));
		}
	}
}

CapexBreakdown Simulator::calculateCapex(const TaskData& taskData) const {
	return calculate_capex(mSiteData, taskData);
}

ReportData Simulator::simulateTimesteps(const TaskData& taskData, SimulationType simulationType) const {
	/* INITIALISE classes that support energy sums and object precedence */
	Config config(taskData);	// flags energy component presence in TaskData & balancing modes
	TempSum tempSum(mSiteData);		// class of arrays for running totals (replace ESUM and Heat)

	ReportData reportData{};

	// Do tariff precalculation
	size_t tariff_index = taskData.grid ? taskData.grid->tariff_index : 0;

	DayTariffStats tariffStats{ mSiteData, tariff_index };


	// Run through the pre balancing loop components

	if (taskData.building) {
		Hotel hotel(mSiteData, taskData.building.value());
		hotel.AllCalcs(tempSum);
		hotel.Report(reportData);
	}

	if (taskData.renewables) {
		BasicPV PV1(mSiteData, taskData.renewables.value());
		PV1.AllCalcs(tempSum);
		PV1.Report(reportData);
	}

	if (config.getEVFlag() == EVFlag::NON_BALANCING) {
		BasicElectricVehicle EV1(mSiteData, taskData.electric_vehicles.value());
		EV1.AllCalcs(tempSum);
		EV1.Report(reportData);
	}

	if (taskData.domestic_hot_water && taskData.heat_pump) {
		HotWaterCylinder hotWaterCylinder{ mSiteData, taskData.domestic_hot_water.value(), taskData.heat_pump.value(), tariff_index, tariffStats };
		hotWaterCylinder.AllCalcs(tempSum);
		hotWaterCylinder.Report(reportData);
	}


	// Construct components that may be in the balancing loop

	std::unique_ptr<ESS> ESSmain;
	if (taskData.energy_storage_system) {
		ESSmain = std::make_unique<BasicESS>(mSiteData, taskData.energy_storage_system.value(), tariff_index, tariffStats);
	}
	else {
		ESSmain = std::make_unique<NullESS>(mSiteData);
	}

	std::unique_ptr<BasicElectricVehicle> EV1;
	if (taskData.electric_vehicles) {
		EV1 = std::make_unique<BasicElectricVehicle>(mSiteData, taskData.electric_vehicles.value());
	}

	// TODO - as we can return an invalid result here, we should do this earlier
	std::unique_ptr<DataCentre> dataCentre;
	std::unique_ptr<AmbientHeatPumpController> ambientController;

	if (taskData.data_centre && taskData.heat_pump && taskData.heat_pump->heat_source == HeatSource::HOTROOM) {
		// make a DataCentre with a hotroom heatpump
		dataCentre = std::make_unique<DataCentreWithASHP>(mSiteData, taskData.data_centre.value(), taskData.heat_pump.value());

	}
	else if (taskData.data_centre && taskData.heat_pump && taskData.heat_pump->heat_source == HeatSource::AMBIENT_AIR) {
		// make a basic data centre (without a heatpump)
		dataCentre = std::make_unique<BasicDataCentre>(mSiteData, taskData.data_centre.value());
		ambientController = std::make_unique<AmbientHeatPumpController>(mSiteData, taskData.heat_pump.value());
	}
	else if (taskData.heat_pump && !taskData.data_centre) {
		ambientController = std::make_unique<AmbientHeatPumpController>(mSiteData, taskData.heat_pump.value());
	}
	else if (taskData.data_centre && !taskData.heat_pump) {
		dataCentre = std::make_unique<BasicDataCentre>(mSiteData, taskData.data_centre.value());
	}


	if (ambientController) {
		ambientController->AllCalcs(tempSum);
	}

	if (config.getDataCentreFlag() == DataCentreFlag::NON_BALANCING) {
		dataCentre->AllCalcs(tempSum);
	}

	// BALANCING LOOP

	float futureEnergy = 0.0f;
	size_t timesteps = mSiteData.timesteps;
	const float availableGridImport = getFixedAvailableImport(taskData);


	auto dcFlag = config.getDataCentreFlag();
	auto evFlag = config.getEVFlag();

	if (dcFlag == DataCentreFlag::BALANCING && evFlag == EVFlag::BALANCING) {
		// This represents the logic in M-VEST v0-7:
		// EV is curtailed before the Data Centre

		for (size_t t = 0; t < timesteps; t++) {
			futureEnergy = availableGridImport + ESSmain->AvailDisch() - dataCentre->getTargetLoad(t);
			EV1->StepCalc(tempSum, futureEnergy, t);
			futureEnergy = availableGridImport + ESSmain->AvailDisch();
			dataCentre->StepCalc(tempSum, futureEnergy, t);
			ESSmain->StepCalc(tempSum, availableGridImport, t);
		}
	}
	else if (dcFlag != DataCentreFlag::BALANCING && evFlag == EVFlag::BALANCING) {
		for (size_t t = 0; t < timesteps; t++) {
			futureEnergy = availableGridImport + ESSmain->AvailDisch();
			EV1->StepCalc(tempSum, futureEnergy, t);
			ESSmain->StepCalc(tempSum, availableGridImport, t);
		}
	}
	else if (dcFlag == DataCentreFlag::BALANCING && evFlag != EVFlag::BALANCING) {
		for (size_t t = 0; t < timesteps; t++) {
			futureEnergy = availableGridImport + ESSmain->AvailDisch();
			dataCentre->StepCalc(tempSum, futureEnergy, t);
			ESSmain->StepCalc(tempSum, availableGridImport, t);
		}
	}
	else {
		for (size_t t = 0; t < timesteps; t++) {
			ESSmain->StepCalc(tempSum, availableGridImport, t);
		}
	}

	// Run through the post balancing loop components

	if (taskData.mop) {
		Mop mop(mSiteData, taskData.mop.value());
		mop.AllCalcs(tempSum);
		mop.Report(reportData);
	}

	if (taskData.grid && taskData.building) {
		Grid grid(mSiteData, taskData.grid.value(), taskData.building.value());
		grid.AllCalcs(tempSum);
		grid.Report(reportData);
	}

	if (taskData.gas_heater) {
		GasCombustionHeater GasCH(mSiteData, taskData.gas_heater.value());
		GasCH.AllCalcs(tempSum);
		GasCH.Report(reportData);
	}

	tempSum.Report(reportData);
	ESSmain->Report(reportData);
	if (config.dataCentrePresent()) {
		dataCentre->Report(reportData);
	}

	if (ambientController) {
		// There is a heatpump and no DataCentre
		ambientController->Report(reportData);
	}

	return reportData;
}

SimulationResult Simulator::makeInvalidResult(const TaskData& taskData) const {
	// When a scenario is invalid, for now we return the FLT_MAX or FLT_MIN for each objective as appropriate

	// TODO - apply proper fix for 'nullable' results
	SimulationResult result{};

	result.project_CAPEX = std::numeric_limits<float>::max();
	result.total_annualised_cost = std::numeric_limits<float>::max();
	result.scenario_cost_balance = std::numeric_limits<float>::lowest();
	result.payback_horizon_years = std::numeric_limits<float>::max();
	result.scenario_carbon_balance_scope_1 = std::numeric_limits<float>::lowest();
	result.scenario_carbon_balance_scope_2 = std::numeric_limits<float>::lowest();

	return result;
}

CostVectors Simulator::extractCostVectors(const ReportData& reportData, const TaskData& taskData) const {
	CostVectors costVectors;

	// If the components that create these vectors are not present then the vectors in reportData may be empty
	// we instead need them to be 0 valued but of timestep length
	costVectors.actual_ev_load_e = reportData.EV_actualload.size() ? reportData.EV_actualload : Eigen::VectorXf::Zero(mSiteData.timesteps);
	costVectors.actual_data_centre_load_e = reportData.Data_centre_actual_load.size() ? reportData.Data_centre_actual_load : Eigen::VectorXf::Zero(mSiteData.timesteps);
	costVectors.building_load_e = reportData.Hotel_load.size() ? reportData.Hotel_load : Eigen::VectorXf::Zero(mSiteData.timesteps);
	costVectors.heatload_h = reportData.Heatload.size() ? reportData.Heatload : Eigen::VectorXf::Zero(mSiteData.timesteps);
	costVectors.gas_import_h = reportData.GasCH_load.size() ? reportData.GasCH_load : Eigen::VectorXf::Zero(mSiteData.timesteps);
	costVectors.grid_import_e = reportData.Grid_Import.size() ? reportData.Grid_Import : Eigen::VectorXf::Zero(mSiteData.timesteps);
	costVectors.grid_export_e = reportData.Grid_Export.size() ? reportData.Grid_Export : Eigen::VectorXf::Zero(mSiteData.timesteps);
	costVectors.actual_low_priority_load_e = reportData.MOP_load.size() ? reportData.MOP_load : Eigen::VectorXf::Zero(mSiteData.timesteps);

	float fixed_export_price = taskData.grid ? taskData.grid->export_tariff : 0.0f;
	costVectors.grid_export_prices = Eigen::VectorXf::Constant(mSiteData.timesteps, fixed_export_price);

	return costVectors;
}


// HACK: the balancing loop needs to know how much is available 
// to import from the Grid but there may not be a grid.
// 
// Because the available import is constant throughout all timesteps when there is a grid
// we can just construct a grid and immediately throw it away to calculate the import available.
// 
// If there is no grid, we instead return 0
//  
float Simulator::getFixedAvailableImport(const TaskData& taskData) const
{
	if (taskData.grid && taskData.building) {
		Grid grid(mSiteData, taskData.grid.value(), taskData.building.value());
		return grid.AvailImport();
	}
	// else 0
	return 0.0f;
}


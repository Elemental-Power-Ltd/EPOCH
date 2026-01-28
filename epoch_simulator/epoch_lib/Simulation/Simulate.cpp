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
#include "Costs/NetPresentValue.hpp"
#include "DayTariffStats.hpp"
#include "Components/DHW/HotWaterCylinder.hpp"
#include "Components/DHW/InstantWaterHeater.hpp"

#include "Flags.hpp"
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
#include "Costs/SAP.hpp"

Simulator::Simulator(SiteData siteData, TaskConfig config):
	mSiteData(siteData),
	mConfig(config)
{

	mBaselineReportData = simulateTimesteps(mSiteData.baseline);
	CostVectors baselineCostVectors = extractCostVectors(mBaselineReportData, mSiteData.baseline);
	mBaselineUsage = calculateBaselineUsage(mSiteData, mConfig, baselineCostVectors);

	mBaselineMetrics = calculateMetrics(mSiteData.baseline, mBaselineReportData, mBaselineUsage);
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

	SimulationResult result{};

	result.report_data = simulateTimesteps(taskData, simulationType);

	const CostVectors& costVectors = extractCostVectors(result.report_data.value(), taskData);

	auto scenarioUsage = calculateScenarioUsage(mSiteData, mConfig, taskData, costVectors);

	result.baseline_metrics = mBaselineMetrics;
	result.metrics = calculateMetrics(taskData, result.report_data.value(), scenarioUsage);
	result.comparison = compareScenarios(mSiteData, mBaselineUsage, result.baseline_metrics, scenarioUsage, result.metrics);
	result.scenario_capex_breakdown = calculateCapexWithDiscounts(taskData);;


	if (simulationType != SimulationType::FullReporting) {
		// We only return the full timeseries vectors in FullReporting mode
		result.report_data = std::nullopt;
		result.baseline_report_data = std::nullopt;
	}
	else {
		// if FullReporting, also set the baseline report data
		result.baseline_report_data = mBaselineReportData;
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

	// check the yield_index is in bounds for each solar panel
	int num_yields = static_cast<int>(mSiteData.solar_yields.size());
	for (const SolarData& solar : taskData.solar_panels) {
		if (solar.yield_index >= num_yields) {
			throw std::runtime_error(std::format(
				"Cannot use yield_index of {} with {} yields provided",
				solar.yield_index, mSiteData.solar_yields.size()
			));
		}
	}
}

CapexBreakdown Simulator::calculateCapexWithDiscounts(const TaskData& taskData) const {
	return calculate_capex_with_discounts(mSiteData, mConfig, taskData);
}

ReportData Simulator::simulateTimesteps(const TaskData& taskData, [[maybe_unused]] SimulationType simulationType) const {
	/* INITIALISE classes that support energy sums and object precedence */
	Flags flags(taskData);	// flags energy component presence in TaskData & balancing modes
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

	if (taskData.solar_panels.size() > 0) {
		BasicPV PV1(mSiteData, taskData.solar_panels);
		PV1.AllCalcs(tempSum);
		PV1.Report(reportData);
	}

	if (flags.getEVFlag() == EVFlag::NON_BALANCING) {
		BasicElectricVehicle EV1(mSiteData, taskData.electric_vehicles.value());
		EV1.AllCalcs(tempSum);
		EV1.Report(reportData);
	}

	bool heatPumpCanSupplyDHW = false;
	if (taskData.domestic_hot_water && taskData.heat_pump) {
		HotWaterCylinder hotWaterCylinder{ mSiteData, taskData.domestic_hot_water.value(), taskData.heat_pump.value(), tariff_index, tariffStats };
		hotWaterCylinder.AllCalcs(tempSum);
		hotWaterCylinder.Report(reportData);
		heatPumpCanSupplyDHW = true;
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
		ambientController = std::make_unique<AmbientHeatPumpController>(mSiteData, taskData.heat_pump.value(), heatPumpCanSupplyDHW);
	}
	else if (taskData.heat_pump && !taskData.data_centre) {
		ambientController = std::make_unique<AmbientHeatPumpController>(mSiteData, taskData.heat_pump.value(), heatPumpCanSupplyDHW);
	}
	else if (taskData.data_centre && !taskData.heat_pump) {
		dataCentre = std::make_unique<BasicDataCentre>(mSiteData, taskData.data_centre.value());
	}


	if (ambientController) {
		ambientController->AllCalcs(tempSum);
	}

	if (flags.getDataCentreFlag() == DataCentreFlag::NON_BALANCING) {
		dataCentre->AllCalcs(tempSum);
	}

	tempSum.ReportBeforeBalancingLoop(reportData);
	// BALANCING LOOP

	float futureEnergy = 0.0f;
	size_t timesteps = mSiteData.timesteps;
	const float availableGridImport = getFixedAvailableImport(taskData);


	auto dcFlag = flags.getDataCentreFlag();
	auto evFlag = flags.getEVFlag();

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

	if (!taskData.gas_heater) {
		// If there's no gas heater, we assume a resistive heating component to meet DHW
		InstantWaterHeater iwh(mSiteData);
		iwh.AllCalcs(tempSum);
		iwh.Report(reportData);
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
	if (flags.dataCentrePresent()) {
		dataCentre->Report(reportData);
	}

	if (ambientController) {
		// There is a heatpump and no DataCentre
		ambientController->Report(reportData);
	}

	return reportData;
}

SimulationResult Simulator::makeInvalidResult([[maybe_unused]] const TaskData& taskData) const {
	// When a scenario is invalid, for now we return the FLT_MAX or FLT_MIN for each objective as appropriate

	// TODO - apply proper fix for 'nullable' results
	SimulationResult result{};

	// comparison metrics
	result.comparison.meter_balance = std::numeric_limits<float>::lowest();
	result.comparison.operating_balance = std::numeric_limits<float>::lowest();
	result.comparison.cost_balance = std::numeric_limits<float>::lowest();
	result.comparison.npv_balance = std::numeric_limits<float>::lowest();
	result.comparison.payback_horizon_years = std::numeric_limits<float>::max();

	result.comparison.carbon_balance_scope_1 = std::numeric_limits<float>::lowest();
	result.comparison.carbon_balance_scope_2 = std::numeric_limits<float>::lowest();
	result.comparison.combined_carbon_balance = std::numeric_limits<float>::lowest();
	result.comparison.carbon_cost = std::numeric_limits<float>::max();

	// select scenario metrics
	result.metrics.total_capex = std::numeric_limits<float>::max();
	result.metrics.total_annualised_cost = std::numeric_limits<float>::max();
	result.metrics.total_scope_1_emissions = std::numeric_limits<float>::max();
	result.metrics.total_scope_2_emissions = std::numeric_limits<float>::max();
	result.metrics.total_combined_carbon_emissions = std::numeric_limits<float>::max();
	result.metrics.total_net_present_value = std::numeric_limits<float>::lowest();

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

SimulationMetrics Simulator::calculateMetrics(const TaskData& taskData, const ReportData& reportData, const UsageData& usage) const {
	SimulationMetrics metrics{};

	// energy totals in kWh
	metrics.total_gas_used = reportData.GasCH_load.sum();
	metrics.total_electricity_imported = reportData.Grid_Import.sum();
	metrics.total_electricity_generated = reportData.PVacGen.sum();
	metrics.total_electricity_exported = reportData.Grid_Export.sum();
	metrics.total_electricity_curtailed = reportData.Actual_curtailed_export.sum();
	metrics.total_electricity_used = 
		(metrics.total_electricity_imported + metrics.total_electricity_generated) 
		- (metrics.total_electricity_exported + metrics.total_electricity_curtailed);

	metrics.total_electrical_shortfall = reportData.Actual_import_shortfall.sum();

	metrics.total_heat_shortfall = reportData.Heat_shortfall.sum();
	metrics.total_ch_shortfall = reportData.CH_shortfall.sum();
	metrics.total_dhw_shortfall = reportData.DHW_Shortfall.sum();

	// calculate the maximum heat our components can produce
	float component_heat = 0.0f;
	if (taskData.gas_heater) {
		component_heat += taskData.gas_heater->maximum_output;
	}
	if (taskData.heat_pump) {
		component_heat += taskData.heat_pump->heat_power;
	}
	// determine the peak_hload given the fabric intervention used
	float required_peak_hload = 0.0f;
	if (taskData.building && taskData.building->fabric_intervention_index != 0) {
		// fabric_intervention_index is a 1-based index, 0 corresponds to building_hload instead
		required_peak_hload = mSiteData.fabric_interventions[taskData.building->fabric_intervention_index - 1].peak_hload;
	}
	else {
		// we default to the baseline peak_hload in instances where there is no Building component
		// and also when no fabric interventions have been applied
		required_peak_hload = mSiteData.peak_hload;
	}
	metrics.peak_hload_shortfall = std::max(required_peak_hload - component_heat, 0.0f);

	metrics.total_ch_load = reportData.CH_demand.sum() - metrics.total_ch_shortfall;
	metrics.total_dhw_load = reportData.DHW_demand.sum() - metrics.total_dhw_shortfall;
	metrics.total_heat_load = metrics.total_dhw_load + metrics.total_ch_load;

	// financial totals in £
	metrics.total_capex = usage.capex_breakdown.total_capex;
	metrics.total_gas_import_cost = usage.fuel_cost;
	metrics.total_electricity_import_cost = usage.elec_cost;
	metrics.total_electricity_export_gain = usage.export_revenue;

	metrics.total_meter_cost = usage.total_meter_cost;
	metrics.total_operating_cost = usage.total_operating_cost;

	auto valueMetrics = calculate_npv(mSiteData, mConfig, taskData, usage);
	metrics.total_annualised_cost = valueMetrics.annualised_cost;
	metrics.total_net_present_value = valueMetrics.net_present_value;

	metrics.total_scope_1_emissions = usage.carbon_scope_1_kg_CO2e;
	metrics.total_scope_2_emissions = usage.carbon_scope_2_kg_CO2e;
	metrics.total_combined_carbon_emissions = usage.carbon_scope_1_kg_CO2e + usage.carbon_scope_2_kg_CO2e;
	
	if (taskData.building.has_value() && taskData.building->floor_area.has_value()) {
		float floor_area = taskData.building->floor_area.value();
		// This is a best approximation of the energy input for SAP
		// (a breakdown of electricity to extract heating, cooling and lighting would be more correct)
		double sap_electricity = metrics.total_electricity_used - metrics.total_electricity_exported;
		double sap_co2 = sap_co2_emissions(metrics.total_gas_used, sap_electricity);
		metrics.environmental_impact_score = environmental_impact_rating(sap_co2, floor_area);
		metrics.environmental_impact_grade = rating_to_band(metrics.environmental_impact_score.value());
	}

	return metrics;
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


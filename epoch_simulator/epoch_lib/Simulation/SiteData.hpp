#pragma once

#include <chrono>
#include <optional>
#include <vector>

#include <Eigen/Core>

#include "../Definitions.hpp"
#include "Fabric.hpp"


struct SiteData {
	SiteData(
		std::chrono::system_clock::time_point start_ts,
		std::chrono::system_clock::time_point end_ts,
		TaskData baseline,
		year_TS building_eload,
		year_TS building_hload,
		float peak_hload,
		year_TS ev_eload,
		year_TS dhw_demand,
		year_TS air_temperature,
		year_TS grid_co2,
		std::vector<year_TS> solar_yields,
		std::vector<year_TS> import_tariffs,
		std::vector<FabricIntervention> fabric_interventions,
		Eigen::MatrixXf ashp_input_table,
		Eigen::MatrixXf ashp_output_table
	)
		: start_ts(start_ts),
		end_ts(end_ts),
		baseline(baseline),
		building_eload(std::move(building_eload)),
		building_hload(std::move(building_hload)),
		peak_hload(peak_hload),
		ev_eload(std::move(ev_eload)),
		dhw_demand(std::move(dhw_demand)),
		air_temperature(std::move(air_temperature)),
		grid_co2(std::move(grid_co2)),
		solar_yields(std::move(solar_yields)),
		import_tariffs(std::move(import_tariffs)),
		fabric_interventions(std::move(fabric_interventions)),
		ashp_input_table(std::move(ashp_input_table)),
		ashp_output_table(std::move(ashp_output_table))
	{
		derive_time_properties();
		validate_site_data();
	}

	std::chrono::system_clock::time_point start_ts;
	std::chrono::system_clock::time_point end_ts;

	// The baseline components for this site
	const TaskData baseline;

	// The electrical demand in kWh/timestep
	year_TS building_eload;
	// The base heating demand in kWh/timestep
	year_TS building_hload;
	// The peak heating load in kW for the baseline (as calculated by an external source such as PHPP)
	float peak_hload;
	// The electric vehicle demand in kWh/timestep
	year_TS ev_eload;
	// The hot water demand in kWh/timestep
	year_TS dhw_demand;
	// The ambient air temperature in degrees celsius
	year_TS air_temperature;
	// The grid carbon intensity in g/kWh
	// This must be converted to kg for most of our metrics
	year_TS grid_co2;

	// The solar yields per timestep for a 1kW peak panel
	std::vector<year_TS> solar_yields;
	// The electrical import prices in pounds / kWh
	std::vector<year_TS> import_tariffs;
	// The (exclusive) fabric intervention options for this site
	std::vector<FabricIntervention> fabric_interventions;

	// The input lookup table for the heatpumps
	Eigen::MatrixXf ashp_input_table;
	// The output lookup table for the heatpumps
	Eigen::MatrixXf ashp_output_table;

	// derived properties
	std::chrono::seconds timestep_interval_s;
	// the length of a timestep in hours
	// (deliberately a float because this is typically used to scale properties expressed in kWh)
	float timestep_hours;
	size_t timesteps;

	void derive_time_properties() {
		// use building_eload for the length of all vectors
		timesteps = this->building_eload.size();

		if (timesteps < 1) {
			throw std::runtime_error("Timeseries must contain values - building_eload is length 0");
		}

		// start_ts should be less than end_ts
		if (!(this->start_ts < this->end_ts)) {
			throw std::runtime_error("start_ts must be less than end_ts");
		}

		auto total_span = this->end_ts - this->start_ts;
		timestep_interval_s = std::chrono::duration_cast<std::chrono::seconds>(
			// deliberately timesteps and not timesteps - 1
			// start_ts is the lower bound of the first timestep
			// end_ts is the upper bound of the final timestep
			total_span / timesteps
		);

		timestep_hours = std::chrono::duration<float>(timestep_interval_s).count() / (60 * 60);
	}

	void validate_site_data() {

		// we're not using the existing timesteps 
		// because the compiler will complain about signed/unsigned mismatch
		auto timestep_size = this->building_eload.size();

		// check that the timeseries are all the same length
		if (this->building_hload.size() != timestep_size
			|| this->ev_eload.size() != timestep_size
			|| this->dhw_demand.size() != timestep_size
			|| this->air_temperature.size() != timestep_size
			|| this->grid_co2.size() != timestep_size)
		{
			throw std::runtime_error("Timeseries must all have the same length");
		}

		// check solar_yield lengths
		for (const auto& s : this->solar_yields) {
			if (s.size() != timestep_size) {
				throw std::runtime_error("Solar yields do not have the correct number of timesteps");
			}
		}

		// check import_tariffs
		if (this->import_tariffs.empty()) {
			throw std::runtime_error("There must be at least one import_tariff");
		}
		for (const auto& t : this->import_tariffs) {
			if (t.size() != timestep_size) {
				throw std::runtime_error("Import tariffs do not have the correct number of timesteps");
			}
		}

		// check fabric_interventions
		for (const auto& fi : this->fabric_interventions) {
			if (fi.reduced_hload.size() != timestep_size) {
				throw std::runtime_error("fabric interventions do not have the correct number of timesteps");
			}
		}

		// heatpump lookup tables must be the same dimensions and at least 2*2
		if (this->ashp_input_table.rows() != this->ashp_output_table.rows()
			|| this->ashp_input_table.cols() != this->ashp_output_table.cols())
		{
			throw std::runtime_error("ashp_input_table and ashp_output_table are not the same size");
		}
		if (this->ashp_input_table.rows() < 2 || this->ashp_input_table.cols() < 2) {
			throw std::runtime_error("heatpump tables must be at least 2x2");
		}
	}
};

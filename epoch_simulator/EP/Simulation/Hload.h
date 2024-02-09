#pragma once

#include <Eigen/Core>

#include "Config.h"
#include "../Definitions.h"
#include "Eload.h"

class Hload
{
public:
	Hload(const HistoricalData& historicalData, const Config& config) :
		mTimesteps(config.calculate_timesteps()),
		mTS_Heatload(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Heat_shortfall(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Heat_surplus(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Scaled_electrical_fix_heat_load_1(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Scaled_electrical_fix_heat_load_2(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Scaled_electrical_highflex_heat_load(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Scaled_electrical_lowflex_heat_load(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Electrical_load_scaled_heat_yield(Eigen::VectorXf::Zero(mTimesteps))
	{}


	void performHeatCalculations(const HistoricalData& historicalData, const Config& config, const Grid& grid) {

		mTS_Heatload = historicalData.heatload_data * config.getScalarHL1();

		// scale historical data by heat hield scalar
		mTS_Scaled_electrical_fix_heat_load_1 = historicalData.hotel_eload_data * config.getScalarHYield1();
		mTS_Scaled_electrical_fix_heat_load_2 = historicalData.ev_eload_data * config.getScalarHYield2();

		calculateElectrical_load_scaled_heat_yield(
			grid.getActualHighPriorityLoad(), grid.getActualLowPriorityLoad(), 
			config.getScalarHYield3(), config.getScalarHYield4()
		);

		//Heat shortfall
		//IF(B4>AB4,B4-AB4,0)
		calculateHeat_shortfall();

		//Heat surplus
		//IF(B4<AB4,AB3-B4,0)
		calculateHeat_surplus();
	}

	void calculateElectrical_load_scaled_heat_yield(const year_TS& TS_Actual_high_priority_load,
		const year_TS& TS_Actual_low_priority_load, float ScalarHYield3, float ScalarHYield4) {

		mTS_Electrical_load_scaled_heat_yield += mTS_Scaled_electrical_fix_heat_load_1;
		mTS_Electrical_load_scaled_heat_yield += mTS_Scaled_electrical_fix_heat_load_2;
		mTS_Electrical_load_scaled_heat_yield += (TS_Actual_high_priority_load * ScalarHYield3);
		mTS_Electrical_load_scaled_heat_yield += (TS_Actual_low_priority_load * ScalarHYield4);
	}

	void calculateHeat_shortfall() {
		for (int index = 0; index < mTimesteps; index++) {
			mTS_Heat_shortfall[index] = std::max(
				mTS_Heatload[index] - mTS_Electrical_load_scaled_heat_yield[index],
				0.0f
			);
		}
	}

	void calculateHeat_surplus() {
		for (int index = 0; index < mTimesteps; index++) {
			mTS_Heat_surplus[index] = std::max(
				mTS_Electrical_load_scaled_heat_yield[index] - mTS_Heatload[index],
				0.0f
			);
		}
	}

		
	year_TS getTS_Heatload() const {
		return mTS_Heatload;
	}

	year_TS getTS_Heat_shortfall() const {
		return mTS_Heat_shortfall;
	}

	year_TS getTS_Heat_surplus() const {
		return mTS_Heat_surplus;
	}

	year_TS getTS_Scaled_electrical_fix_heat_load_1() const {
		return mTS_Scaled_electrical_fix_heat_load_1;
	}

	year_TS getTS_Scaled_electrical_fix_heat_load_2() const {
		return mTS_Scaled_electrical_fix_heat_load_2;
	}

	year_TS getTS_Scaled_electrical_highflex_heat_load() const {
		return mTS_Scaled_electrical_highflex_heat_load;
	}

	year_TS getTS_Scaled_electrical_lowflex_heat_load() const {
		return mTS_Scaled_electrical_lowflex_heat_load;
	}

	year_TS getTS_Electrical_load_scaled_heat_yield() const {
		return mTS_Electrical_load_scaled_heat_yield;
	}


private:
	const int mTimesteps;

	year_TS mTS_Heatload;
	year_TS mTS_Heat_shortfall;
	year_TS mTS_Heat_surplus;
	year_TS mTS_Scaled_electrical_fix_heat_load_1; 
	year_TS mTS_Scaled_electrical_fix_heat_load_2; 
	year_TS mTS_Scaled_electrical_highflex_heat_load;
	year_TS mTS_Scaled_electrical_lowflex_heat_load;
	year_TS mTS_Electrical_load_scaled_heat_yield;
};


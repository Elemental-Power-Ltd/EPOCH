#pragma once

#include <Eigen/Core>

#include "TaskData.hpp"
#include "../Definitions.hpp"
#include "Eload.hpp"

class Hload
{
public:
	Hload(const HistoricalData& historicalData, const TaskData& taskData) :
		mTimesteps(taskData.calculate_timesteps()),
		mHeatload(Eigen::VectorXf::Zero(mTimesteps)),
		mHeatShortfall(Eigen::VectorXf::Zero(mTimesteps)),
		mHeatSurplus(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalFixHeatLoad_1(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalFixHeatLoad_2(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalHighFlexHeatLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalLowFlexHeatLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mElectricalLoadScaledHeatYield(Eigen::VectorXf::Zero(mTimesteps))
	{}


	void performHeatCalculations(const HistoricalData& historicalData, const TaskData& taskData, const Grid& grid) {

		mHeatload = historicalData.heatload_data * taskData.ScalarHL1;

		// scale historical data by heat hield scalar
		mScaledElectricalFixHeatLoad_1 = historicalData.hotel_eload_data * taskData.ScalarHYield1;
		mScaledElectricalFixHeatLoad_2 = historicalData.ev_eload_data * taskData.ScalarHYield2;

		calculateElectricalLoadScaledHeatYield(
			grid.getActualHighPriorityLoad(), grid.getActualLowPriorityLoad(), 
			taskData.ScalarHYield3, taskData.ScalarHYield4
		);

		//Heat shortfall
		//IF(B4>AB4,B4-AB4,0)
		calculateHeatShortfall();

		//Heat surplus
		//IF(B4<AB4,AB3-B4,0)
		calculateHeatSurplus();
	}

	void calculateElectricalLoadScaledHeatYield(const year_TS& ActualHighPriorityLoad,
		const year_TS& ActualLowPriorityLoad, float ScalarHYield3, float ScalarHYield4) {

		mElectricalLoadScaledHeatYield += mScaledElectricalFixHeatLoad_1;
		mElectricalLoadScaledHeatYield += mScaledElectricalFixHeatLoad_2;
		mElectricalLoadScaledHeatYield += (ActualHighPriorityLoad * ScalarHYield3);
		mElectricalLoadScaledHeatYield += (ActualLowPriorityLoad * ScalarHYield4);
	}

	void calculateHeatShortfall() {
		for (int index = 0; index < mTimesteps; index++) {
			mHeatShortfall[index] = std::max(
				mHeatload[index] - mElectricalLoadScaledHeatYield[index],
				0.0f
			);
		}
	}

	void calculateHeatSurplus() {
		for (int index = 0; index < mTimesteps; index++) {
			mHeatSurplus[index] = std::max(
				mElectricalLoadScaledHeatYield[index] - mHeatload[index],
				0.0f
			);
		}
	}

		
	year_TS getHeatload() const {
		return mHeatload;
	}

	year_TS getHeatShortfall() const {
		return mHeatShortfall;
	}

	year_TS getHeatSurplus() const {
		return mHeatSurplus;
	}

	year_TS getScaledElectricalFixHeatLoad_1() const {
		return mScaledElectricalFixHeatLoad_1;
	}

	year_TS getScaledElectricalFixHeatLoad_2() const {
		return mScaledElectricalFixHeatLoad_2;
	}

	year_TS getScaledElectricalHighFlexHeatLoad() const {
		return mScaledElectricalHighFlexHeatLoad;
	}

	year_TS getScaledElectricalLowFlexHeatLoad() const {
		return mScaledElectricalLowFlexHeatLoad;
	}

	year_TS getElectricalLoadScaledHeatYield() const {
		return mElectricalLoadScaledHeatYield;
	}


private:
	const int mTimesteps;

	year_TS mHeatload;
	year_TS mHeatShortfall;
	year_TS mHeatSurplus;
	year_TS mScaledElectricalFixHeatLoad_1; 
	year_TS mScaledElectricalFixHeatLoad_2; 
	year_TS mScaledElectricalHighFlexHeatLoad;
	year_TS mScaledElectricalLowFlexHeatLoad;
	year_TS mElectricalLoadScaledHeatYield;
};


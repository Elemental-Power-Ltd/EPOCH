#pragma once

#include <Eigen/Core>

#include "TaskData.hpp"
#include "../Definitions.hpp"


class Eload {

public:
	Eload(const HistoricalData& historicalData, const TaskData& TaskData)
	{
		int timesteps = TaskData.calculate_timesteps();

		year_TS fixLoad1 = historicalData.hotel_eload_data * TaskData.Fixed_load1_scalar;
		year_TS fixLoad2 = historicalData.ev_eload_data * TaskData.Fixed_load2_scalar;
		mTotalFixLoad = fixLoad1 + fixLoad2;

		year_TS ESSAuxLoad = Eigen::VectorXf::Constant(timesteps, TaskData.ESS_aux_load);
		year_TS targetHighLoad = Eigen::VectorXf::Constant(timesteps, TaskData.Flex_load_max);
		year_TS totalTargetLoad = mTotalFixLoad + targetHighLoad;

		// Add timeseries for (small) parasitic load of ESS
		mTotalLoad = totalTargetLoad + ESSAuxLoad;
	};

	year_TS getTotalFixLoad() const {
		return mTotalFixLoad;
	}

	year_TS getTotalLoad() const {
		return mTotalLoad;
	}


private:
	year_TS mTotalFixLoad;
	year_TS mTotalLoad;
};

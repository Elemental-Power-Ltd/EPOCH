#pragma once

#include <Eigen/Core>

#include "Config.h"
#include "../Definitions.h"


class Eload {

public:
	Eload(const HistoricalData& historicalData, const Config& config)
	{
		int timesteps = config.calculate_timesteps();

		year_TS fixLoad1 = historicalData.hotel_eload_data * config.getFixed_load1_scalar();
		year_TS fixLoad2 = historicalData.ev_eload_data * config.getFixed_load2_scalar();
		mTotal_fix_load = fixLoad1 + fixLoad2;

		year_TS ESS_aux_load = Eigen::VectorXf::Constant(timesteps, config.getESS_aux_load());
		year_TS targetHighLoad = Eigen::VectorXf::Constant(timesteps, config.getFlex_load_max());
		year_TS totalTargetLoad = mTotal_fix_load + targetHighLoad;

		// Add timeseries for (small) parasitic load of ESS
		mTotal_load = totalTargetLoad + ESS_aux_load;
	};

	year_TS getTS_Total_fix_load() const {
		return mTotal_fix_load;
	}

	year_TS getTS_Total_load() const {
		return mTotal_load;
	}


private:
	year_TS mTotal_fix_load;
	year_TS mTotal_load;
};

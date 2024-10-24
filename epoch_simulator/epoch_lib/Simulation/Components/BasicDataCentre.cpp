#include "DataCentre.hpp"

BasicDataCentre::BasicDataCentre(const HistoricalData& historicalData, const TaskData& taskData) :
	DataCentre(historicalData, taskData),
	mTimesteps(taskData.calculate_timesteps()),
	// Mode: 1=Target, 2=Price, 3=Carbon
	mOptimisationMode(1),
	// Max kWh per TS
	mDataCentreMaxLoad_e(taskData.Flex_load_max* taskData.timestep_hours),

	mTargetLoad_e(Eigen::VectorXf::Zero(mTimesteps)),
	mActualLoad_e(Eigen::VectorXf::Zero(mTimesteps))
{
	// Calculate Target Load based on the optimisation mode: 1=Target (default), 2=Price, 3=Carbon
	switch (mOptimisationMode) {
	case 2: // Price minimisation mode
		// placeholder for lookahead supplier price mode
	case 3: // Carbon minimisation mode
		// placholder for lookahead grid carbon mode
	default: // Target Power Mode (initially Max Load)							
		mTargetLoad_e.setConstant(mDataCentreMaxLoad_e);
	}
}

void BasicDataCentre::AllCalcs(TempSum& tempSum) {
	// If Data Centre  is not balancing, actual loads will be target
	mActualLoad_e = mTargetLoad_e;
	// update Temp Energy Balances
	tempSum.Elec_e += mActualLoad_e;

}

void BasicDataCentre::StepCalc(TempSum& tempSum, const float futureEnergy_e, const int t) {
	if (futureEnergy_e <= 0) {
		mActualLoad_e[t] = 0;
	}
	else if (futureEnergy_e > mTargetLoad_e[t]) {
		// Set Load & Budget to maximums
		mActualLoad_e[t] = mTargetLoad_e[t];
	}
	else {
		// Reduce Load & Budget to largest without breaching FutureEnergy
		mActualLoad_e[t] = futureEnergy_e;
	}
	// Update Temp Energy Balances
	tempSum.Elec_e[t] += mActualLoad_e[t];
}


float BasicDataCentre::getTargetLoad(int timestep) {
	return mTargetLoad_e[timestep];
}

void BasicDataCentre::Report(ReportData& reportData) const {
	reportData.Data_centre_target_load = mTargetLoad_e;
	reportData.Data_centre_actual_load = mActualLoad_e;

	// TODO - FIXME
	// The way that ReportData is structured, we assume that we always have all of the vectors
	// The following vectors are specific to a data centre with an ASHP (which we don't have in this case)
	// So we write them as 0 vectors mimicking the length of the other results
	// (consider changing reporting from a struct with fixed vectors to a map of String->year_TS?
	reportData.Data_centre_target_heat = Eigen::VectorXf::Zero(mTargetLoad_e.size());
	reportData.Data_centre_available_hot_heat = Eigen::VectorXf::Zero(mTargetLoad_e.size());


}

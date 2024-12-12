#include "DataCentre.hpp"

DataCentreWithASHP::DataCentreWithASHP(const HistoricalData& historicalData, const DataCentreData& dc, const HeatPumpData& hp):
	DataCentre(historicalData),
	mHeatPump(historicalData, hp, dc),
	mTimesteps(historicalData.timesteps),
	mOptimisationMode(DataCentreOptimisationMode::Target),
	// Max kWh per TS
	mDataCentreMaxLoad_e(dc.maximum_load * historicalData.timestep_hours),
	// Percentage of waste heat captured for ASHP
	mHeatScalar(SCALAR_HEAT_YIELD),

	mTargetLoad_e(Eigen::VectorXf::Zero(mTimesteps)),
	mActualLoad_e(Eigen::VectorXf::Zero(mTimesteps)),
	mAvailableHotHeat_h(Eigen::VectorXf::Zero(mTimesteps)),
	mTargetHeat_h(Eigen::VectorXf::Zero(mTimesteps))
{

	// Calculate Target Load based on the optimisation mode: 1=Target (default), 2=Price, 3=Carbon
	switch (mOptimisationMode) {
	case DataCentreOptimisationMode::Target:
		mTargetLoad_e.setConstant(mDataCentreMaxLoad_e);
		break;
	case DataCentreOptimisationMode::Price:
		// placeholder for lookahead supplier price mode
		throw std::logic_error("Not Implemented");
		break;
	case DataCentreOptimisationMode::Carbon:
		// placholder for lookahead grid carbon mode
		throw std::logic_error("Not Implemented");
		break;
	}
}

void DataCentreWithASHP::AllCalcs(TempSum& tempSum) {
	// If Data Centre  is not balancing, actual loads will be target
	mActualLoad_e = mTargetLoad_e;
	mAvailableHotHeat_h = mActualLoad_e * mHeatScalar;
	// FUTURE can switch TargetHeat to Pool, DHW or combo
	// mTargetHeat_h = tempSum.Heat_h; REMOVED to support DHW & CH
	mHeatPump.AllCalcs(tempSum, mAvailableHotHeat_h);

	// update Temp Energy Balances
	tempSum.Elec_e += mActualLoad_e;
}

void DataCentreWithASHP::StepCalc(TempSum& tempSum, const float futureEnergy_e, const size_t t) {
	// Switch to Pool, DHW, CH done in HeatPump
	// mTargetHeat_h[t] = tempSum.Heat_h[t];REMOVED to support DHW & CH

	float heatpumpMaxElectricalLoad = mHeatPump.MaxElec(t);

	// Set Electricty Budget for ASHP
	float heatPumpBudget_e;
	if (futureEnergy_e <= 0) {
		mActualLoad_e[t] = 0;
		heatPumpBudget_e = 0;
	}
	else if (futureEnergy_e > (mTargetLoad_e[t] + heatpumpMaxElectricalLoad)) {
		// Set Load & Budget to maximums
		mActualLoad_e[t] = mTargetLoad_e[t];
		heatPumpBudget_e = futureEnergy_e - mTargetLoad_e[t];
	}
	else {
		// Reduce Load & Budget to largest without breaching FutureEnergy
		float throttleScalar = futureEnergy_e / (mTargetLoad_e[t] + heatpumpMaxElectricalLoad);
		mActualLoad_e[t] = mTargetLoad_e[t] * throttleScalar;
		heatPumpBudget_e = futureEnergy_e - mActualLoad_e[t];
	}
	// Set hot heat (beyond ambient) available from DataCentre
	mAvailableHotHeat_h[t] = mActualLoad_e[t] * mHeatScalar;

	mHeatPump.StepCalc(tempSum, mAvailableHotHeat_h[t], heatPumpBudget_e, t);

	// Update Temp Energy Balances
	tempSum.Elec_e[t] += mActualLoad_e[t];
}

float DataCentreWithASHP::getTargetLoad(size_t timestep) {
	return mTargetLoad_e[timestep];
}

void DataCentreWithASHP::Report(ReportData& reportData) const {
	reportData.Data_centre_target_load = mTargetLoad_e;
	reportData.Data_centre_actual_load = mActualLoad_e;
	// TODO - investigate mTargetHeat_h (is it always 0?)
	reportData.Data_centre_target_heat = mTargetHeat_h;
	reportData.Data_centre_available_hot_heat = mAvailableHotHeat_h;

	// TODO report heatpump results

}




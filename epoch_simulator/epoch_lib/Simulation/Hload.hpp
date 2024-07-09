#pragma once

#include <Eigen/Core>

#include "TaskData.hpp"
#include "../Definitions.hpp"
#include "Eload.hpp"
#include "HeatPump.hpp"

class Hload {

public:
	Hload(const HistoricalData& historicalData, const TaskData& taskData) :
		mTimesteps(taskData.calculate_timesteps()),
		mHeatPump(historicalData, taskData),
		mHeatload(Eigen::VectorXf::Zero(mTimesteps)),
		mHeatShortfall(Eigen::VectorXf::Zero(mTimesteps)),
		mEHeatSurplus(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalFixHeatLoad_1(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalFixHeatLoad_2(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalHighFlexHeatLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalLowFlexHeatLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mElectricalLoadScaledHeatYield(Eigen::VectorXf::Zero(mTimesteps)),
		mMaxHeatpumpOutput(Eigen::VectorXf::Zero(mTimesteps)),
		mMaxHeatpumpELoad(Eigen::VectorXf::Zero(mTimesteps)),
		mASHPTargetLoading(Eigen::VectorXf::Zero(mTimesteps)),
		mActualHeatpumpOutput(Eigen::VectorXf::Zero(mTimesteps))
	{
	}

	void performHeatCalculations(const HistoricalData& historicalData, const TaskData& taskData) {

		mHeatload = historicalData.heatload_data * taskData.ScalarHL1;

		calculateMaxHeatpumpOutput(historicalData, taskData);
		
		calculateMaxHeatpumpELoad(historicalData, taskData);

		calculateASHPTargetLoading();

		calculateHeatShortfall();

		calculateTarget_Data_centre_ASHP_load(taskData);
	}

	void calculateElectricalLoadScaledHeatYield(const year_TS& ActualHighPriorityLoad,
		const year_TS& ActualLowPriorityLoad, float ScalarHYield3, float ScalarHYield4) {

		mElectricalLoadScaledHeatYield += mScaledElectricalFixHeatLoad_1;
		mElectricalLoadScaledHeatYield += mScaledElectricalFixHeatLoad_2;
		mElectricalLoadScaledHeatYield += (ActualHighPriorityLoad * ScalarHYield3);
		mElectricalLoadScaledHeatYield += (ActualLowPriorityLoad * ScalarHYield4);
	}

	// calculate the minimum data centre load to provide adequate heat source
	void calculateTarget_Data_centre_ASHP_load(const TaskData& taskData)
	{
		mTargetDatacentreASHPload = mMaxHeatpumpELoad.array() * getASHPTargetLoading().array() + taskData.Flex_load_max;
	}

	void calculateMaxHeatpumpOutput(const HistoricalData& historicalData, const TaskData& taskData)
	{ 
	
		for (int index = 0; index < mTimesteps; index++) // main loop where index is timestep
		{
			mMaxHeatpumpOutput[index] = mHeatPump.getOutput(historicalData.airtemp_data[index]);
		};
	}

	void calculateMaxHeatpumpELoad(const HistoricalData& historicalData, const TaskData& taskData)
	{
		switch (mHeatPump.getHeatSource()) {
		case HeatSource::AMBIENT_AIR:
			for (int index = 0; index < mTimesteps; index++) {
				mMaxHeatpumpELoad[index] = mHeatPump.getAmbientInput(historicalData.airtemp_data[index]);
			}
			break;
		case HeatSource::HOTROOM:
			mMaxHeatpumpELoad.setConstant(mHeatPump.getHotroomInput());
			break;
		}
	}

	// Calculate the ideal ASHP electricity load for the entire heat demand
	// (if subsequently electricity load cannot be fully met, data centre and ASHP eload will be reduced in lockstep)
	void calculateASHPTargetLoading()
	{
		// heatload divided by heatpump output, capped at 1.0
		mASHPTargetLoading = (mHeatload.array() / mMaxHeatpumpOutput.array()).min(1.0f);
	}

	void calculateActualHeatpumpOutput(const year_TS& Data_Centre_HP_load_scalar)
	{
		mActualHeatpumpOutput = Data_Centre_HP_load_scalar.array() * mMaxHeatpumpOutput.array() * mASHPTargetLoading.array();
	}

	void calculateHeatShortfall() {
		mHeatShortfall = mHeatload - mActualHeatpumpOutput;
	}

	void calculateEHeatSurplus(const year_TS& Actual_low_priority_load) 
	{
		mEHeatSurplus = Actual_low_priority_load;
			
	}

	void calculateHeatSUM(const year_TS& data_Centre_HP_load_scalar, const year_TS& actualLowPriorityLoad) {

		calculateActualHeatpumpOutput(data_Centre_HP_load_scalar);

		calculateHeatShortfall();

		calculateEHeatSurplus(actualLowPriorityLoad);
	}

		
	year_TS getHeatload() const {
		return mHeatload;
	}

	year_TS getHeatShortfall() const {
		return mHeatShortfall;
	}

	year_TS getEHeatSurplus() const {
		return mEHeatSurplus;
	}

	year_TS getElectricalLoadScaledHeatYield() const {
		return mElectricalLoadScaledHeatYield;
	}

	year_TS getMaxHeatpumpELoad() const {
		return mMaxHeatpumpELoad;
	}

	year_TS getASHPTargetLoading() const {
		return mASHPTargetLoading;
	}

	year_TS getTargetDatacentreASHPload() const {
		return mTargetDatacentreASHPload;
	}


private:
	const int mTimesteps;

	HeatPump mHeatPump;

	year_TS mHeatload;
	year_TS mHeatShortfall;
	year_TS mEHeatSurplus;
	year_TS mScaledElectricalFixHeatLoad_1; 
	year_TS mScaledElectricalFixHeatLoad_2; 
	year_TS mScaledElectricalHighFlexHeatLoad;
	year_TS mScaledElectricalLowFlexHeatLoad;
	year_TS mElectricalLoadScaledHeatYield;
	year_TS mMaxHeatpumpOutput;
	year_TS mMaxHeatpumpELoad;
	year_TS mASHPTargetLoading;
	year_TS mActualHeatpumpOutput;
	year_TS mTargetDatacentreASHPload;

};


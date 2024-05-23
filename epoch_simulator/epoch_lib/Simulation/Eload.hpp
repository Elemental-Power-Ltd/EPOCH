#pragma once

#include <Eigen/Core>

#include "TaskData.hpp"
#include "../Definitions.hpp"

class Eload {

public:
	Eload(const HistoricalData& historicalData, const TaskData& taskData) :
		mFixLoad1(Eigen::VectorXf::Zero(mTimesteps)),
		mEVLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mTimesteps(taskData.calculate_timesteps()),
		mActual_EV_load(Eigen::VectorXf::Zero(mTimesteps)),
		mActual_Data_Centre_ASHP_load(Eigen::VectorXf::Zero(mTimesteps)),
		mSelf_consume_pre_EV_flex(Eigen::VectorXf::Zero(mTimesteps)),
		mTotal_target_load_fixed_flex(Eigen::VectorXf::Zero(mTimesteps)),
		mData_Centre_HP_load_scalar(Eigen::VectorXf::Zero(mTimesteps)),
		mActual_Data_Centre_load(Eigen::VectorXf::Zero(mTimesteps)),
		mActual_ASHP_load(Eigen::VectorXf::Zero(mTimesteps)),
		mTotalBaselineFixLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mTargetHighLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mTotalBaselineELoad(Eigen::VectorXf::Zero(mTimesteps))
	{
			mFixLoad1 = historicalData.hotel_eload_data * taskData.Fixed_load1_scalar;
			mEVLoad = historicalData.ev_eload_data * taskData.Fixed_load2_scalar;

			mTotalBaselineFixLoad = mFixLoad1 + mEVLoad;

			mTargetHighLoad = Eigen::VectorXf::Constant(mTimesteps, taskData.Flex_load_max);
			mTotalBaselineELoad = mTotalBaselineFixLoad + mTargetHighLoad;

			mHeadroomL1 = taskData.Import_headroom * mFixLoad1.maxCoeff();
	}
	
	year_TS calculateActual_EV_load(const TaskData& taskData)
	{
		
		for (int index = 0; index < mTimesteps; index++)
		{
			if (mSelf_consume_pre_EV_flex[index] > 0)
			{
				if (mSelf_consume_pre_EV_flex[index] > (mEVLoad[index] * taskData.EV_flex))
				{
					mActual_EV_load[index] = mEVLoad[index] * (1 - taskData.EV_flex);
				}
				else
				{
					mActual_EV_load[index] = mEVLoad[index] - mSelf_consume_pre_EV_flex[index];
				}
			}
			else
			{
				mActual_EV_load[index] = mEVLoad[index];
			}
			
		}
	
		return mActual_EV_load;
	}

	year_TS calculateActual_Data_Centre_ASHP_load(const year_TS& Pre_flex_shortfall, const year_TS& Target_Data_Centre_ASHP_load)
	{
		for (int index = 0; index < mTimesteps; index++) {
			if (Pre_flex_shortfall[index] > Target_Data_Centre_ASHP_load[index])
			{
				mActual_Data_Centre_ASHP_load[index] = 0;
			}
			else 
			{
				mActual_Data_Centre_ASHP_load[index] = Target_Data_Centre_ASHP_load[index] - Pre_flex_shortfall[index];
			}

		}
		return mActual_Data_Centre_ASHP_load;
	}

	void calculateData_Centre_HP_load_scalar(const year_TS& Target_Data_Centre_ASHP_load)
	{
		mData_Centre_HP_load_scalar = mActual_Data_Centre_ASHP_load.array() / Target_Data_Centre_ASHP_load.array();
	}

	void calculateSelf_consume_pre_EV_flex(const year_TS& TargetDatacentreASHPload, const year_TS& ESSAuxLoad, const year_TS& RGen_total)
	{
		mSelf_consume_pre_EV_flex = mFixLoad1 + mEVLoad + TargetDatacentreASHPload + ESSAuxLoad - RGen_total;
	}

	void calculateActual_Data_Centre_load(float flex_load_max)
	{
		mActual_Data_Centre_load = mData_Centre_HP_load_scalar.array() * flex_load_max;
	}

	void calculateActual_ASHP_load(const year_TS& ASHPTargetLoading, const year_TS& MaxHeatpumpELoad)
	{
		mActual_ASHP_load = mData_Centre_HP_load_scalar.array() * ASHPTargetLoading.array() * MaxHeatpumpELoad.array();
	}


	void calculateTotal_target_load_fixed_flex(const year_TS& TargetDatacentreASHPload, const year_TS& ESSAuxLoad)
	{
		mTotal_target_load_fixed_flex = mFixLoad1 + mActual_EV_load + TargetDatacentreASHPload + ESSAuxLoad;
	}

	void calculateTotalBaselineFixLoad()
	{
		mTotalBaselineFixLoad = mFixLoad1 + mActual_EV_load;
	}
	
	year_TS getTotalLoad() const {
		return mTotalLoad;
	}


	year_TS gettargetHighLoad() const {
		return mTargetHighLoad;
	}

	year_TS getSelf_consume_pre_EV_flex() const {
		return mSelf_consume_pre_EV_flex;
	}

	year_TS getTotal_target_load_fixed_flex() const {
		return mTotal_target_load_fixed_flex;
	}

	year_TS getFixLoad1() const {
		return mFixLoad1;
	}

	year_TS getmEVLoad() const {
		return mEVLoad;
	}

	year_TS getTotalBaselineFixLoad() const {
		return mTotalBaselineFixLoad;
	}

	year_TS getActual_Data_Centre_ASHP_load() const {
		return mActual_Data_Centre_ASHP_load;
	}

	year_TS getData_Centre_HP_load_scalar() const {
		return mData_Centre_HP_load_scalar;
	}

	year_TS getActual_Data_Centre_load() const {
		return mActual_Data_Centre_load;
	}

	year_TS getActual_ASHP_load() const {
		return mActual_ASHP_load;
	}

	float getHeadroomL1() const {
		return mHeadroomL1;
	}



private:
	float mHeadroomL1;
	int mTimesteps;

	year_TS mFixLoad1;
	year_TS mEVLoad;

	year_TS mTotalLoad;

	year_TS mTargetHighLoad;
	year_TS mSelf_consume_pre_EV_flex;
	year_TS mTotal_target_load_fixed_flex;
	year_TS mTotalBaselineELoad;
	year_TS mTotalBaselineFixLoad;
	year_TS mActual_EV_load;
	year_TS mActual_Data_Centre_ASHP_load;
	year_TS mData_Centre_HP_load_scalar;
	year_TS mActual_Data_Centre_load;
	year_TS mActual_ASHP_load;
	
};

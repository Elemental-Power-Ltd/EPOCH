#pragma once

#include <Eigen/Core>

#include "TaskData.hpp"
#include "../Definitions.hpp"
#include "Eload.hpp"

class Hload {

public:
	Hload(const HistoricalData& historicalData, const TaskData& taskData) :
		mTimesteps(taskData.calculate_timesteps()),
		mHeatload(Eigen::VectorXf::Zero(mTimesteps)),
		mHeatShortfall(Eigen::VectorXf::Zero(mTimesteps)),
		mEHeatSurplus(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalFixHeatLoad_1(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalFixHeatLoad_2(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalHighFlexHeatLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mScaledElectricalLowFlexHeatLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mElectricalLoadScaledHeatYield(Eigen::VectorXf::Zero(mTimesteps)),
		mAmbientAirTemperature(Eigen::VectorXf::Zero(mTimesteps)),
		mMaxHeatpumpOutputAmbientAir(Eigen::VectorXf::Zero(mTimesteps)),
		mMaxHeatpumpOutputHotroomAir(Eigen::VectorXf::Zero(mTimesteps)),
		mMaxHeatpumpELoad(Eigen::VectorXf::Zero(mTimesteps)),
		mASHPTargetLoadingAmbientAir(Eigen::VectorXf::Zero(mTimesteps)),
		mASHPTargetLoadingHotroomAir(Eigen::VectorXf::Zero(mTimesteps)),
		mActualHeatpumpOutput(Eigen::VectorXf::Zero(mTimesteps)),

		mASHPTamb(Eigen::VectorXf::Zero(13)), // size can be dynmically set depending on number of rows in Lookup table
		mASHPperkWHeatOut(Eigen::VectorXf::Zero(13)), // size can be dynmically set depending on number of rows in Lookup table
		mASHPperkWPowerIn(Eigen::VectorXf::Zero(13)),  // size can be dynmically set depending on number of rows in Lookup table
		
		mASHPRadTemp_lookup(0.0f),
		mASHPreference_Hpower(14.0f),
		mASHPHot_Hpower_max(0.0f),
		mASHPHot_Epower_max(0.0f),
		mASHPtable_col_index(0),
		mASHP_HSource(taskData.ASHP_HSource)
	{}

	void performHeatCalculations(const HistoricalData& historicalData, const TaskData& taskData) {

		mHeatload = historicalData.heatload_data * taskData.ScalarHL1;

		mAmbientAirTemperature = historicalData.airtemp_data;

		calculateASHPcolumn_index(historicalData, taskData);

		//if (taskData.ASHP_HSource == 1)
	//	{
			calculateMaxHeatpumpOutputAmbientAir(historicalData, taskData);
			//float sum = mMaxHeatpumpOutputAmbientAir.sum(); // check this calculated correctly
	//	}
	//	if (taskData.ASHP_HSource == 2)
	//	{
			calculateMaxHeatpumpOutputHotroomAir(historicalData, taskData);
			//float sum2 = mMaxHeatpumpOutputHotroomAir.sum(); //check this calculated correctly
	//	}
		
		calculateMaxHeatpumpELoad(historicalData, taskData);

		calculateASHPTargetLoading();

		//Heat shortfall
		//IF(B4>AB4,B4-AB4,0)
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

	void calculateTarget_Data_centre_ASHP_load(const TaskData& taskData)
	{
		mTargetDatacentreASHPload = mMaxHeatpumpELoad.cwiseProduct(getASHPTargetLoading()).array() + taskData.Flex_load_max;
	}

	void calculateASHPcolumn_index(const HistoricalData& historicalData, const TaskData& taskData)
	{
		for (int inner_index = 1; inner_index < 14; inner_index++)
		{
			mASHPTamb[inner_index - 1] = historicalData.ASHPinputtable[0][inner_index]; // skip index 0 as is column header in ASHPinputtable
		}
		 // this is references the column of the ASHP lookup table (=Radiator temp)

		for (int outer_index = 1; outer_index < 14; outer_index++) // start at 1, 0 is header
		{

			if (taskData.ASHP_RadTemp <= historicalData.ASHPinputtable[outer_index][0]) // looking for match from task Rad_temp to HP table Rad_temp less than or equal)
			{
				mASHPRadTemp_lookup = historicalData.ASHPinputtable[outer_index][0]; // snap back to discretised Rad temp in lookup table for now
				mASHPtable_col_index = outer_index; // column we need corresponding to rad temp for main lookup
				break;
			}
		}
	}

	void calculateMaxHeatpumpOutputAmbientAir(const HistoricalData& historicalData, const TaskData& taskData)
	{ 
	
		for (int index = 0; index < mTimesteps; index++) // main loop where index is timestep
		{
			for (int inner_index = 1; inner_index < 14; inner_index++) // inner_index corresponds to row of HP lookup table with Ambient Air source temp
			{
				if (mAmbientAirTemperature[index] < historicalData.ASHPinputtable[0][1]) // this simply sets ASHP output to minimum if air temp is below min of -15 (not robust as HP may lock out)
				{
					mMaxHeatpumpOutputAmbientAir[index] = historicalData.ASHPoutputtable[mASHPtable_col_index][inner_index] * taskData.ASHP_HPower / mASHPreference_Hpower;
					break;
				}
				if (mAmbientAirTemperature[index] < historicalData.ASHPinputtable[0][inner_index]) // how you know you want the row: [inner_index - 1]
				{
					mMaxHeatpumpOutputAmbientAir[index] = historicalData.ASHPoutputtable[mASHPtable_col_index][inner_index-1] * taskData.ASHP_HPower / mASHPreference_Hpower; // Scale by modelled HP power, and descale by HP look up table is for reference model power  
					break;																																					 				
				}
			}
		};
	}

	void calculateMaxHeatpumpOutputHotroomAir(const HistoricalData& historicalData, const TaskData& taskData)
	{

		// in case of hotroom the temperature is fixed
		
		for (int inner_index = 1; inner_index < 14; inner_index++) // inner_index corresponds to row of HP lookup table with Hot room source temp
			{
				if (taskData.ASHP_HotTemp < historicalData.ASHPinputtable[0][1]) // this simply sets ASHP output to minimum if Hot room temp is below min of -15 (not robust as HP may lock out)
				{
					mASHPHot_Hpower_max = historicalData.ASHPoutputtable[mASHPtable_col_index][inner_index];
					break;
				}
				if (taskData.ASHP_HotTemp < historicalData.ASHPinputtable[0][inner_index]) // how you know you want the row: [inner_index - 1]
				{
					mASHPHot_Hpower_max = historicalData.ASHPoutputtable[mASHPtable_col_index][inner_index - 1]; // Scale by modelled HP power, and descale by HP look up table is for reference model power  
					break;
				}
				if (taskData.ASHP_HotTemp == historicalData.ASHPinputtable[0][inner_index]) // how you know you want the row: [inner_index - 1]
				{
					mASHPHot_Hpower_max = historicalData.ASHPoutputtable[mASHPtable_col_index][inner_index]; // Scale by modelled HP power, and descale by HP look up table is for reference model power  
					break;
				}
				if (taskData.ASHP_HotTemp > historicalData.ASHPinputtable[0][13]) // how you know you want the row: [inner_index - 1]
				{
					mASHPHot_Hpower_max = historicalData.ASHPoutputtable[mASHPtable_col_index][13]; // Scale by modelled HP power, and descale by HP look up table is for reference model power  
					break;
				}

			}
		// main loop that sets hotroom max
			
		for (int index = 0; index < mTimesteps; index++)
		{
			mMaxHeatpumpOutputHotroomAir[index] = std::min((mMaxHeatpumpOutputAmbientAir[index] + (taskData.Flex_load_max * taskData.ScalarHYield)), (mASHPHot_Hpower_max * taskData.ASHP_HPower / mASHPreference_Hpower));
		}
	}

	void calculateMaxHeatpumpELoad(const HistoricalData& historicalData, const TaskData& taskData)
	{
		if (mASHP_HSource == 1) // if the ASHP source is ambient air
		{
			for (int index = 0; index < mTimesteps; index++) // main loop where index is timestep
			{
				for (int inner_index = 1; inner_index < 14; inner_index++) // inner_index corresponds to row of HP lookup table with Ambient Air source temp
				{
					if (mAmbientAirTemperature[index] < historicalData.ASHPinputtable[0][1]) // this simply sets ASHP output to minimum if air temp is below min of -15 (not robust as HP may lock out)
					{
						mMaxHeatpumpELoad[index] = historicalData.ASHPinputtable[mASHPtable_col_index][inner_index] * taskData.ASHP_HPower / mASHPreference_Hpower;
						break;
					}
					if (mAmbientAirTemperature[index] < historicalData.ASHPinputtable[0][inner_index]) // how you know you want the row: [inner_index - 1]
					{
						mMaxHeatpumpELoad[index] = historicalData.ASHPinputtable[mASHPtable_col_index][inner_index - 1] * taskData.ASHP_HPower / mASHPreference_Hpower; // Scale by modelled HP power, and descale by HP look up table is for reference model power  
						break;
					}
				}
			}
		}
		if (mASHP_HSource == 2) // if the ASHP source is hotroom air
		{
			for (int inner_index = 1; inner_index < 14; inner_index++) // inner_index corresponds to row of HP lookup table with Hot room source temp
			{
				if (taskData.ASHP_HotTemp < historicalData.ASHPinputtable[0][1]) // this simply sets ASHP output to minimum if Hot room temp is below min of -15 (not robust as HP may lock out)
				{
					mASHPHot_Epower_max = historicalData.ASHPinputtable[mASHPtable_col_index][inner_index];
					break;
				}
				if (taskData.ASHP_HotTemp < historicalData.ASHPinputtable[0][inner_index]) // how you know you want the row: [inner_index - 1]
				{
					mASHPHot_Epower_max = historicalData.ASHPinputtable[mASHPtable_col_index][inner_index - 1]; // Scale by modelled HP power, and descale by HP look up table is for reference model power  
					break;
				}
				if (taskData.ASHP_HotTemp == historicalData.ASHPinputtable[0][inner_index]) // how you know you want the row: [inner_index - 1]
				{
					mASHPHot_Epower_max = historicalData.ASHPinputtable[mASHPtable_col_index][inner_index]; // Scale by modelled HP power, and descale by HP look up table is for reference model power  
					break;
				}
				if (taskData.ASHP_HotTemp > historicalData.ASHPinputtable[0][13]) // how you know you want the row: [inner_index - 1]
				{
					mASHPHot_Epower_max = historicalData.ASHPinputtable[mASHPtable_col_index][13]; // Scale by modelled HP power, and descale by HP look up table is for reference model power  
					break;
				}

			}
			// main loop that sets HPEloadMax if hotroom

			for (int index = 0; index < mTimesteps; index++)
			{
				mMaxHeatpumpELoad[index] = mASHPHot_Epower_max * taskData.ASHP_HPower / mASHPreference_Hpower;
			}
		}
		
	}

	void calculateASHPTargetLoading()
	{
		if (mASHP_HSource == 1) // if the ASHP source is ambient air
		{
			for (int index = 0; index < mTimesteps; index++)
			{
				mASHPTargetLoadingAmbientAir[index] = mHeatload[index]/ mMaxHeatpumpOutputAmbientAir[index];
				if (mASHPTargetLoadingAmbientAir[index] > 1.0) // cap at 100%
					mASHPTargetLoadingAmbientAir[index] = 1.0;
			}
		}

		if (mASHP_HSource == 2) // if the ASHP source is ambient air
		{
			for (int index = 0; index < mTimesteps; index++)
			{
				mASHPTargetLoadingHotroomAir[index] = mHeatload[index] / mMaxHeatpumpOutputHotroomAir[index];
				if (mASHPTargetLoadingHotroomAir[index] > 1.0)  // cap at 100%
					mASHPTargetLoadingHotroomAir[index] = 1.0;
			}
		}

	}

	year_TS calculateActualHeatpumpOutput(const year_TS& Data_Centre_HP_load_scalar)
	{
		if (mASHP_HSource == 1) // if the ASHP source is ambient air
		{
			for (int index = 0; index < mTimesteps; index++)
			{
				mActualHeatpumpOutput[index] = Data_Centre_HP_load_scalar[index] * mMaxHeatpumpOutputAmbientAir[index] * mASHPTargetLoadingAmbientAir[index];
				
			}
		}

		if (mASHP_HSource == 2) // if the ASHP source is ambient air
		{
			for (int index = 0; index < mTimesteps; index++)
			{
				mActualHeatpumpOutput[index] = Data_Centre_HP_load_scalar[index] * mMaxHeatpumpOutputHotroomAir[index] * mASHPTargetLoadingHotroomAir[index];
				
			}
		}
		return mActualHeatpumpOutput;
	}


	void calculateHeatShortfall() {
		for (int index = 0; index < mTimesteps; index++)
		{
			mHeatShortfall[index] = mHeatload[index] - mActualHeatpumpOutput[index];
		}
	}

	void calculateEHeatSurplus(const year_TS& Actual_low_priority_load) 
	{
		mEHeatSurplus = Actual_low_priority_load;
			
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

	year_TS getAmbientAirTemperature() const {
		return mAmbientAirTemperature;
	}

	year_TS getMaxHeatpumpELoad() const {
		return mMaxHeatpumpELoad;
	}

	year_TS getASHPTargetLoadingAmbientAir() const {
		return mASHPTargetLoadingAmbientAir;
	}

	year_TS getASHPTargetLoadingHotroomAir() const {
		return mASHPTargetLoadingHotroomAir;
	}

	year_TS getASHPTargetLoading() const {
		
		if (mASHP_HSource == 1)
			return mASHPTargetLoadingAmbientAir;

		if (mASHP_HSource ==2)
			return mASHPTargetLoadingHotroomAir;
	}

	year_TS getActualHeatpumpOutput() const {
		return mActualHeatpumpOutput;
	}

	year_TS getTargetDatacentreASHPload() const {
		return mTargetDatacentreASHPload;
	}


private:
	const int mTimesteps;

	year_TS mHeatload;
	year_TS mHeatShortfall;
	year_TS mEHeatSurplus;
	year_TS mScaledElectricalFixHeatLoad_1; 
	year_TS mScaledElectricalFixHeatLoad_2; 
	year_TS mScaledElectricalHighFlexHeatLoad;
	year_TS mScaledElectricalLowFlexHeatLoad;
	year_TS mElectricalLoadScaledHeatYield;
	year_TS mAmbientAirTemperature;
	year_TS mMaxHeatpumpOutputAmbientAir;
	year_TS mMaxHeatpumpOutputHotroomAir;
	year_TS mMaxHeatpumpELoad;
	year_TS mASHPTargetLoadingAmbientAir;
	year_TS mASHPTargetLoadingHotroomAir;
	year_TS mActualHeatpumpOutput;
	year_TS mTargetDatacentreASHPload;

	Eigen::VectorXf mASHPTamb;
	Eigen::VectorXf mASHPperkWHeatOut;
	Eigen::VectorXf mASHPperkWPowerIn;

	float mASHPRadTemp_lookup;
	float mASHPreference_Hpower; // the reference heating power for the ASHP lookup, based on SAMSUNG AE140BXYDGG/EU 14 kWtherm
	float mASHPHot_Hpower_max;
	float mASHPHot_Epower_max;

	int mASHPtable_col_index;
	const int mASHP_HSource;
};


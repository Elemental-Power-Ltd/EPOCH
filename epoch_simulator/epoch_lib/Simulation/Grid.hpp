#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "Assets.hpp"
#include "TaskData.hpp"
#include "../Definitions.hpp"

class Grid
{
public:
	Grid(const TaskData& taskData): 
		mMaxGridImportkVA(taskData.GridImport),
		mMaxGridExportkVA(taskData.GridExport),
		mMinPowerFactor(taskData.Min_power_factor),
		mImportHeadroom(taskData.Import_headroom),
		mExportHeadroom(taskData.Export_headroom),
		mTimesteps(taskData.calculate_timesteps()),
		mFlexLoadMax(taskData.Flex_load_max),
		mMopLoadMax(taskData.Mop_load_max),

		mGridImport(Eigen::VectorXf::Zero(mTimesteps)),
		mGridExport(Eigen::VectorXf::Zero(mTimesteps)),
		mPreGridBalance(Eigen::VectorXf::Zero(mTimesteps)),
		mPostGridBalance(Eigen::VectorXf::Zero(mTimesteps)),
		mPreFlexImportShortfall(Eigen::VectorXf::Zero(mTimesteps)),
		mPreMopCurtailedExport(Eigen::VectorXf::Zero(mTimesteps)),
		mActualImportShortfall(Eigen::VectorXf::Zero(mTimesteps)),
		mActualCurtailedExport(Eigen::VectorXf::Zero(mTimesteps)),

		mActualHighPriorityLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mActualLowPriorityLoad(Eigen::VectorXf::Zero(mTimesteps))
	{}

	void performGridCalculations(const year_TS& ESUM, const ESS& ess, float HeadroomL1, const year_TS& ASHPTargetLoading, const year_TS& HeatpumpELoad) {

		// calculate the pre-grid balance
		mPreGridBalance = ESUM - ess.getESSDischarge() + ess.getESSCharge();

		//Calculate Grid Import = IF(BB4>0,MIN(BB4,Grid_imp),0)
		calculateGridImport(HeadroomL1);

		//Calculate Grid Export = IF(BB4<0,MIN(-BB4,Grid_exp),0)
		calculateGridExport();

		//Calculate Post-grid balance = BB4-B4+AB4
		mPostGridBalance = mPreGridBalance - mGridImport + mGridExport;

		float mPostGridBalancesum = mPostGridBalance.sum();

		//Calulate Pre-Flex Import shortfall = IF(CB>0, CB4, 0)
		calculatePreFlexImportShortfall();

		float mPreFlexImportShortfallsum = mPreFlexImportShortfall.sum();

		//Calculate Pre-Mop Curtailed Export = IF(CB<0,-CB4,0)
		calculatePreMopCurtailedExport();

		float mPreMopCurtailedExportsum = mPreMopCurtailedExport.sum();

		//Actual Import shortfall (load curtailment) = IF(DB4>ESum!DB4,DB4-ESum!DB4,0)
		calculateActualImportShortfall(ASHPTargetLoading, HeatpumpELoad);

		float mActualImportShortfallsum = mActualImportShortfall.sum();

		//Actual Curtailed Export = IF(EB>ESum!EB4,EB4-ESum!EB4,0)
		calculateActualCurtailedExport();

		float mActualCurtailedExportsum = mActualCurtailedExport.sum();

		calculateActualHighPriorityLoad();

		calculateActualLowPriorityLoad();

		float ActualLowPriorityLoadsum = mActualLowPriorityLoad.sum();
	}


	// Functionality
	// these functions account for headroom built in to Grid_connection to take import/export power peaks intratimestep, and minimum power factor 
	float calculate_Grid_imp(float HeadroomL1) const {
		float Grid_imp = mMaxGridImportkVA * mMinPowerFactor - HeadroomL1;// *(1 - mImportHeadroom);
		return Grid_imp;
	}

	float calculate_Grid_exp() const {
		float Grid_exp = mMaxGridExportkVA * mMinPowerFactor;// *(1 - mExportHeadroom);
		return Grid_exp;
	}

	//Calculate Grid Import = IF(BB4>0,MIN(BB4,Grid_imp),0)
	void calculateGridImport(float HeadroomL1) {
		float gridImp = calculate_Grid_imp(HeadroomL1);

		for (int index = 0; index < mTimesteps; index++) {
			if (mPreGridBalance[index] > 0) {
				mGridImport[index] = std::min(mPreGridBalance[index], gridImp);;
			} else {
				mGridImport[index] = 0;
			}
		}
	}

	//Calculate Grid Export = IF(BB4<0,MIN(-BB4,Grid_exp),0)
	void calculateGridExport() {
		float gridExp = calculate_Grid_exp();

		for (int index = 0; index < mTimesteps; index++) {
			if (mPreGridBalance[index] < 0) {
				mGridExport[index] = std::min(-1.0f * mPreGridBalance[index], gridExp);
			} else {
				mGridExport[index] = 0;
			}
		}
	}

	//Calulate Pre-Flex Import shortfall = IF(CB>0, CB4, 0)
	void calculatePreFlexImportShortfall() {
		for (int index = 0; index < mTimesteps; index++) {
			mPreFlexImportShortfall[index] = std::max(mPostGridBalance[index], 0.0f);
		}
	}

	//Calculate Pre-Mop Curtailed Export = IF(CB<0,-CB4,0)
	void calculatePreMopCurtailedExport() {
		for (int index = 0; index < mTimesteps; index++) {
			mPreMopCurtailedExport[index] = std::min(mPostGridBalance[index], 0.0f);
		}
		// we want the positive counterpart at each timestep, so multiply the vector by -1
		mPreMopCurtailedExport *= -1.0f;
	}

	//Calculate actual Import shortfall (load curtailment) = IF(DB4>ESum!DB4,DB4-ESum!DB4,0)
	void calculateActualImportShortfall(const year_TS& ASHPTargetLoading, const year_TS& HeatpumpELoad) {
		for (int index = 0; index < mTimesteps; index++) {
			mActualImportShortfall[index] = std::max
				(mPreFlexImportShortfall[index] - ((ASHPTargetLoading[index] * (HeatpumpELoad[index]) + mFlexLoadMax)),
				0.0f);
				
		}
	}

	void calculateActualCurtailedExport() {
		for (int index = 0; index < mTimesteps; index++) {
			mActualCurtailedExport[index] = std::max(
				mPreMopCurtailedExport[index] - mMopLoadMax,
				0.0f
			);
		}
	}

	void calculateActualHighPriorityLoad() {
		for (int index = 0; index < mTimesteps; index++) {
			mActualHighPriorityLoad[index] = std::max(
				mFlexLoadMax - mPreFlexImportShortfall[index],
				0.0f
			);
		}
	}

	void calculateActualLowPriorityLoad() {
		for (int index = 0; index < mTimesteps; index++) {
			mActualLowPriorityLoad[index] = std::min(mPreMopCurtailedExport[index], mMopLoadMax);
		}
	}

	year_TS getGridImport() const {
		return mGridImport;
	}

	year_TS getGridExport() const {
		return mGridExport;
	}

	year_TS getPreGridBalance() const {
		return mPreGridBalance;
	}

	year_TS getPostGridBalance() const {
		return mPostGridBalance;
	}

	year_TS getPreFlexImportShortfall() const {
		return mPreFlexImportShortfall;
	}

	year_TS getPreMopCurtailedExport() const {
		return mPreMopCurtailedExport;
	}

	year_TS getActualImportShortfall() const {
		return mActualImportShortfall;
	}

	year_TS getActualCurtailedExport() const {
		return mActualCurtailedExport;
	}

	year_TS getActualHighPriorityLoad() const {
		return mActualHighPriorityLoad;
	}

	year_TS getActualLowPriorityLoad() const {
		return mActualLowPriorityLoad;
	}

private:
	const float mMaxGridImportkVA;
	const float mMaxGridExportkVA;
	const float mMinPowerFactor;
	const float mImportHeadroom;
	const float mExportHeadroom;
	const int mTimesteps;
	const float mFlexLoadMax;
	const float mMopLoadMax;

	year_TS mGridImport;
	year_TS mGridExport;
	year_TS mPreGridBalance;
	year_TS mPostGridBalance;
	year_TS mPreFlexImportShortfall;
	year_TS mPreMopCurtailedExport;
	year_TS mActualImportShortfall;
	year_TS mActualCurtailedExport;
	year_TS mActualHighPriorityLoad;
	year_TS mActualLowPriorityLoad;
};


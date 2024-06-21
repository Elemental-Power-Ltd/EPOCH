#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "Assets.hpp"
#include "Hload.hpp"
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

	void performGridCalculations(const year_TS& ESUM, const ESS& ess, const Hload& hload, float HeadroomL1) {

		// calculate the pre-grid balance
		mPreGridBalance = ESUM - ess.getESSDischarge() + ess.getESSCharge();

		//Calculate Grid Import = IF(BB4>0,MIN(BB4,Grid_imp),0)
		calculateGridImport(HeadroomL1);

		//Calculate Grid Export = IF(BB4<0,MIN(-BB4,Grid_exp),0)
		calculateGridExport();

		//Calculate Post-grid balance = BB4-B4+AB4
		mPostGridBalance = mPreGridBalance - mGridImport + mGridExport;

		//Calulate Pre-Flex Import shortfall = IF(CB>0, CB4, 0)
		calculatePreFlexImportShortfall();

		//Calculate Pre-Mop Curtailed Export = IF(CB<0,-CB4,0)
		calculatePreMopCurtailedExport();

		//Actual Import shortfall (load curtailment) = IF(DB4>ESum!DB4,DB4-ESum!DB4,0)
		calculateActualImportShortfall(hload.getASHPTargetLoading(), hload.getMaxHeatpumpELoad());

		//Actual Curtailed Export = IF(EB>ESum!EB4,EB4-ESum!EB4,0)
		calculateActualCurtailedExport();

		calculateActualHighPriorityLoad();

		calculateActualLowPriorityLoad();
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

		// clamp the grid import between 0 and gridImp at each timestep
		mGridImport = mPreGridBalance.cwiseMax(0.0f).cwiseMin(gridImp);
	}

	//Calculate Grid Export = IF(BB4<0,MIN(-BB4,Grid_exp),0)
	void calculateGridExport() {
		float gridExp = calculate_Grid_exp();

		// flip the preGridBalance then clamp between 0 and gridExp at each timestep
		mGridExport = -1.0f * mPreGridBalance;
		mGridExport = mGridExport.cwiseMax(0.0f).cwiseMin(gridExp);
	}

	//Calulate Pre-Flex Import shortfall = IF(CB>0, CB4, 0)
	void calculatePreFlexImportShortfall() {
		mPreFlexImportShortfall = mPostGridBalance.cwiseMax(0.0f);
	}

	//Calculate Pre-Mop Curtailed Export = IF(CB<0,-CB4,0)
	void calculatePreMopCurtailedExport() {
		mPreMopCurtailedExport = mPostGridBalance.cwiseMin(0.0f);
		// we want the positive counterpart at each timestep, so multiply the vector by -1
		mPreMopCurtailedExport *= -1.0f;
	}

	//Calculate actual Import shortfall (load curtailment) = IF(DB4>ESum!DB4,DB4-ESum!DB4,0)
	void calculateActualImportShortfall(const year_TS& ASHPTargetLoading, const year_TS& HeatpumpELoad) {
		mActualImportShortfall = mActualImportShortfall.array() - mFlexLoadMax - (ASHPTargetLoading.array() * HeatpumpELoad.array());
		mActualImportShortfall = mActualImportShortfall.cwiseMax(0);
	}

	void calculateActualCurtailedExport() {
		// preMopCurtailedExport - MopLoadMax, floored at 0
		mActualCurtailedExport = (mPreMopCurtailedExport.array() - mMopLoadMax).cwiseMin(0.0f);
	}

	void calculateActualHighPriorityLoad() {
		mActualHighPriorityLoad = (mFlexLoadMax - mPreFlexImportShortfall.array()).cwiseMax(0.0f);
	}

	void calculateActualLowPriorityLoad() {
		mActualLowPriorityLoad = mPreMopCurtailedExport.cwiseMin(mMopLoadMax);
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


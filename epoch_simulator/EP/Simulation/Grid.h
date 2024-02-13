#pragma once

#include <Eigen/Core>

#include "Assets.h"
#include "Config.h"
#include "../Definitions.h"

class Grid
{
public:
	Grid(const Config& config): 
		mGridImport(config.getGridImport()),
		mGridExport(config.getGridExport()),
		mImportHeadroom(config.getImport_headroom()),
		mExportHeadroom(config.getExport_headroom()),
		mTimesteps(config.calculate_timesteps()),
		mFlexLoadMax(config.getFlex_load_max()),
		mMopLoadMax(config.getMop_load_max()),

		mTS_GridImport(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_GridExport(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Pre_grid_balance(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Post_grid_balance(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Pre_flex_import_shortfall(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Pre_Mop_curtailed_Export(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Actual_import_shortfall(Eigen::VectorXf::Zero(mTimesteps)),
		mTS_Actual_curtailed_export(Eigen::VectorXf::Zero(mTimesteps)),

		mActualHighPriorityLoad(Eigen::VectorXf::Zero(mTimesteps)),
		mActualLowPriorityLoad(Eigen::VectorXf::Zero(mTimesteps))
	{}

	void performGridCalculations(const year_TS& ESUM, const ESS& ess) {

		// calculate the pre-grid balance
		mTS_Pre_grid_balance = ESUM - ess.getTS_ESS_discharge() + ess.getTS_ESS_charge();

		//Calculate Grid Import = IF(BB4>0,MIN(BB4,Grid_imp),0)
		calculateGridImport();

		//Calculate Grid Export = IF(BB4<0,MIN(-BB4,Grid_exp),0)
		calculateGridExport();

		//Calculate Post-grid balance = BB4-B4+AB4
		mTS_Post_grid_balance = mTS_Pre_grid_balance - mTS_GridImport + mTS_GridExport;

		//Calulate Pre-Flex Import shortfall = IF(CB>0, CB4, 0)
		calculatePre_flex_import_shortfall();

		//Calculate Pre-Mop Curtailed Export = IF(CB<0,-CB4,0)
		calculatePre_Mop_curtailed_Export();

		//Actual Import shortfall (load curtailment) = IF(DB4>ESum!DB4,DB4-ESum!DB4,0)
		calculateActual_import_shortfall();

		//Actual Curtailed Export = IF(EB>ESum!EB4,EB4-ESum!EB4,0)
		calculateActual_curtailed_export();

		calculateActualHighPriorityLoad();
		calculateActualLowPriorityLoad();
	}


	// Functionality
	// these functions account for headroom built in to Grid_connection to take import/export power peaks intratimestep
	float calculate_Grid_imp() const {
		float Grid_imp = mGridImport * (1 - mImportHeadroom);
		return Grid_imp;
	}

	float calculate_Grid_exp() const {
		float Grid_exp = mGridExport * (1 - mExportHeadroom);
		return Grid_exp;
	}

	//Calculate Grid Import = IF(BB4>0,MIN(BB4,Grid_imp),0)
	void calculateGridImport() {
		float gridImp = calculate_Grid_imp();

		for (int index = 0; index < mTimesteps; index++) {
			if (mTS_Pre_grid_balance[index] > 0) {
				mTS_GridImport[index] = std::min(mTS_Pre_grid_balance[index], gridImp);;
			} else {
				mTS_GridImport[index] = 0;
			}
		}
	}

	//Calculate Grid Export = IF(BB4<0,MIN(-BB4,Grid_exp),0)
	void calculateGridExport() {
		float gridExp = calculate_Grid_exp();

		for (int index = 0; index < mTimesteps; index++) {
			if (mTS_Pre_grid_balance[index] < 0) {
				mTS_GridExport[index] = std::min(-1.0f * mTS_Pre_grid_balance[index], gridExp);
			} else {
				mTS_GridExport[index] = 0;
			}
		}
	}

	//Calulate Pre-Flex Import shortfall = IF(CB>0, CB4, 0)
	void calculatePre_flex_import_shortfall() {
		for (int index = 0; index < mTimesteps; index++) {
			mTS_Pre_flex_import_shortfall[index] = std::max(mTS_Post_grid_balance[index], 0.0f);
		}
	}

	//Calculate Pre-Mop Curtailed Export = IF(CB<0,-CB4,0)
	void calculatePre_Mop_curtailed_Export() {
		for (int index = 0; index < mTimesteps; index++) {
			mTS_Pre_Mop_curtailed_Export[index] = std::min(mTS_Post_grid_balance[index], 0.0f);
		}
		// we want the positive counterpart at each timestep, so multiply the vector by -1
		mTS_Pre_Mop_curtailed_Export *= -1.0f;
	}

	//Calculate actual Import shortfall (load curtailment) = IF(DB4>ESum!DB4,DB4-ESum!DB4,0)
	void calculateActual_import_shortfall() {
		for (int index = 0; index < mTimesteps; index++) {
			mTS_Actual_import_shortfall[index] = std::max(
				mTS_Pre_flex_import_shortfall[index] - mFlexLoadMax,
				0.0f
			);
		}
	}

	void calculateActual_curtailed_export() {
		for (int index = 0; index < mTimesteps; index++) {
			mTS_Actual_curtailed_export[index] = std::max(
				mTS_Pre_Mop_curtailed_Export[index] - mMopLoadMax,
				0.0f
			);
		}
	}

	void calculateActualHighPriorityLoad() {
		for (int index = 0; index < mTimesteps; index++) {
			mActualHighPriorityLoad[index] = std::max(
				mFlexLoadMax - mTS_Pre_flex_import_shortfall[index],
				0.0f
			);
		}
	}

	void calculateActualLowPriorityLoad() {
		for (int index = 0; index < mTimesteps; index++) {
			mActualLowPriorityLoad[index] = std::min(mTS_Pre_Mop_curtailed_Export[index], mMopLoadMax);
		}
	}

	year_TS getTS_GridImport() const {
		return mTS_GridImport;
	}

	year_TS getTS_GridExport() const {
		return mTS_GridExport;
	}

	year_TS getTS_Pre_grid_balance() const {
		return mTS_Pre_grid_balance;
	}

	year_TS getTS_Post_grid_balance() const {
		return mTS_Post_grid_balance;
	}

	year_TS getTS_Pre_flex_import_shortfall() const {
		return mTS_Pre_flex_import_shortfall;
	}

	year_TS getTS_Pre_Mop_curtailed_Export() const {
		return mTS_Pre_Mop_curtailed_Export;
	}

	year_TS getTS_Actual_import_shortfall() const {
		return mTS_Actual_import_shortfall;
	}

	year_TS getTS_Actual_curtailed_export() const {
		return mTS_Actual_curtailed_export;
	}

	year_TS getActualHighPriorityLoad() const {
		return mActualHighPriorityLoad;
	}

	year_TS getActualLowPriorityLoad() const {
		return mActualLowPriorityLoad;
	}


private:
	const float mGridImport;
	const float mGridExport;
	const float mImportHeadroom;
	const float mExportHeadroom;
	const int mTimesteps;
	const float mFlexLoadMax;
	const float mMopLoadMax;

	year_TS mTS_GridImport;
	year_TS mTS_GridExport;
	year_TS mTS_Pre_grid_balance;
	year_TS mTS_Post_grid_balance;
	year_TS mTS_Pre_flex_import_shortfall;
	year_TS mTS_Pre_Mop_curtailed_Export;
	year_TS mTS_Actual_import_shortfall;
	year_TS mTS_Actual_curtailed_export;

	year_TS mActualHighPriorityLoad;
	year_TS mActualLowPriorityLoad;
};


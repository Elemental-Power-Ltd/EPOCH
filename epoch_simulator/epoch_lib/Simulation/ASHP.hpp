#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "TaskData.hpp"
#include "../Definitions.hpp"
#include "ASHPperf.hpp"






// ASHPhot is only used within an DataC or alternative heat waste object
class ASHPhot_cl {

public:
	ASHPhot_cl(const HistoricalData& historicalData, const TaskData& taskData) :
		// Initialise Persistent Values
		mASHPperf(taskData),
		TScount(taskData.calculate_timesteps()),
		PowerScalar(taskData.timestep_hours),
		HotTemp(taskData.ASHP_HotTemp),
		AmbientC(historicalData.airtemp_data),	// Ambient Temperature

		// Initilaise results data vectors with all values to zero
		Load_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP electrical load
		Heat_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP heat output
		FreeHeat_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),	// ASHP heat from ambient
		UsedHotHeat_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps()))	// ASHP heat from Hotroom
	{		
		ASHPmaxAmb.Heat_h = 0;	// For mASHPperf->Lookup results
		ASHPmaxAmb.Load_e = 0;
		ASHPmaxHot.Heat_h = 0;
		ASHPmaxHot.Load_e = 0;
	}

	const float MaxElec() {
		// Lookup max possible ASHP electrical load
		return mASHPperf.MaxElecLoad();
	}

	void AllCalcs(const year_TS& TargetHeat_h, const year_TS& AvailHotHeat_h) {
		for(int t = 1; t <= TScount; t++) {
			mASHPperf.Lookup(AmbientC[t], ASHPmaxAmb);	// 2nd Arg is return values struct
			mASHPperf.Lookup(HotTemp, ASHPmaxHot);		// 2nd Arg is return values struct
			
			// If TargetHeat < ASHPmax = lower of Hotroom & Ambient+CoE (Conservation of Energy value)
			ASHPmax_h = std::min((ASHPmaxAmb.Heat_h + AvailHotHeat_h[t]), ASHPmaxHot.Heat_h);
			if(TargetHeat_h[t] <= ASHPmax_h) {
				Heat_h[t] = TargetHeat_h[t];
				Load_e[t] = ASHPmaxHot.Load_e * TargetHeat_h[t] / ASHPmaxHot.Heat_h;
			}
			else {	// ASHP cannot meet TargetHeat, so use values from lower of Hotroom & Amb+CoE
				if(ASHPmaxAmb.Heat_h <= ASHPmaxHot.Heat_h) {
					Heat_h[t] = ASHPmaxAmb.Heat_h;
					Load_e[t] = ASHPmaxAmb.Load_e;
				}
				else {
					Heat_h[t] = ASHPmaxHot.Heat_h;
					Load_e[t] = ASHPmaxHot.Load_e;
				}
			}
		}
		FreeHeat_h = Heat_h - Load_e - AvailHotHeat_h;	// How much heat from ambient
		FreeHeat_h.cwiseMax(0.0f);	// Prevent -ve values where not all AvailHotHeat_h was required
		UsedHotHeat_h = Heat_h - Load_e - FreeHeat_h;
	}

	void StepCalc(const float TargetHeat_h, const float AvailHotHeat_h, const float ElecBudget_e, int t) {
		if(ElecBudget_e <= 0) {
			// No electricty available for the ASHP
			Heat_h[t] = 0;
			Load_e[t] = 0;
		}
		else {
			// Calculate the best the ASHP can do to meet target heat
			mASHPperf.Lookup(AmbientC[t], ASHPmaxAmb);	// 2nd Arg is return values struct
			mASHPperf.Lookup(HotTemp, ASHPmaxHot);		// 2nd Arg is return values struct
			// if TargetHeat < ASHPmax = lower of Hotroom & Ambient+CoE (Conservation of Energy value)
			ASHPmax_h = std::min((ASHPmaxAmb.Heat_h + AvailHotHeat_h), ASHPmaxHot.Heat_h);
			if(TargetHeat_h <= ASHPmax_h) {
				Heat_h[t] = TargetHeat_h;
				Load_e[t] = ASHPmaxHot.Load_e * TargetHeat_h / ASHPmaxHot.Heat_h;
			}
			else {	// ASHP cannot meet TargetHeat, so use values from lower of Hotroom & Amb+CoE
				if(ASHPmaxAmb.Heat_h <= ASHPmaxHot.Heat_h) {
					Heat_h[t] = ASHPmaxAmb.Heat_h;
					Load_e[t] = ASHPmaxAmb.Load_e;
				}
				else {
					Heat_h[t] = ASHPmaxHot.Heat_h;
					Load_e[t] = ASHPmaxHot.Load_e;
				}
			}
			if(Load_e[t] > ElecBudget_e) {
				// Check whether the ASHP load exceeds the electricity budget, if so, reduce proportionally
				Heat_h[t] = Heat_h[t] * ElecBudget_e / Load_e[t];
				Load_e[t] = ElecBudget_e;
			}
		}
	}

	// Public output data, create private ASHP object in parent
	year_TS Load_e;
	year_TS Heat_h;
	year_TS FreeHeat_h;
	year_TS UsedHotHeat_h;

private:
	ASHPperf_cl mASHPperf;
	
	const int TScount;
	const float PowerScalar;
	const int HotTemp;
	float ASHPmax_h;

	const year_TS AmbientC;	// Local ambient temperatures for calcs TS

	ASHP_HE_st ASHPmaxAmb;	// Max Heat & Elec for Ambient input - Struct: 2x TS
	ASHP_HE_st ASHPmaxHot;	// Max Heat & Elec for Hotroom input - Struct: 2x TS
};
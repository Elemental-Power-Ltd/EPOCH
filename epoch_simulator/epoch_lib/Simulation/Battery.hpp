#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "../Definitions.hpp"

// Battery is only used within an ESS or other component with electricity storage
class Battery_cl {

public:
	Battery_cl(const BattData_st BattData) :
		Capacity_e(BattData.Capacity),
		PreSoC_e(BattData.StartSoC_ratio* BattData.Capacity), // Init State of Charge in kWhs
		RTLrate(1.0f - BattData.RTE_ratio), // loss rate easier in calcs
		ChargMax_e(BattData.Charge_power * BattData.PowerScalar), // kWh per timestep
		DischMax_e(BattData.Discharge_power * BattData.PowerScalar), // UkWh per timestep
		AuxLoad_e(BattData.Aux_power * BattData.PowerScalar), // kWh per timestep

		// Initilaise results data vectors with all values to zero
		HistSoC_e(Eigen::VectorXf::Zero(BattData.TScount)),      // Resulting State of Charge per timestep
		HistCharg_e(Eigen::VectorXf::Zero(BattData.TScount)),   // Charge kWh per timestep
		HistDisch_e(Eigen::VectorXf::Zero(BattData.TScount)),   // Discharge kWh per timestep
		HistRTL_e(Eigen::VectorXf::Zero(BattData.TScount)),     // Round trip loss kWh per timestep
		HistAux_e(Eigen::VectorXf::Zero(BattData.TScount))     // Auxiliary Load kWh per timestep
	{
		// Auxiliary same every timestep: is there a vector function for this?
		for (int t = 1; t <= BattData.TScount; t++) {
			HistAux_e[t] = AuxLoad_e;
		}
	}

	float AvailCharg() const {
		return std::min(ChargMax_e, (Capacity_e - PreSoC_e) / (1 - RTLrate));
	}

	float AvailDisch() const {
		return std::min(DischMax_e, PreSoC_e);
	}

	float GetSoC() { return PreSoC_e; }

	void DoCharg(float Charge_e, int t) {
		HistCharg_e[t] = Charge_e;
		HistRTL_e[t] = Charge_e * RTLrate;
		HistSoC_e[t] = PreSoC_e + Charge_e - HistRTL_e[t];
		PreSoC_e = HistSoC_e[t];			//for next timestep
	}

	void DoDisch(float DisCharge_e, int t) {
		HistDisch_e[t] = DisCharge_e;
		HistSoC_e[t] = PreSoC_e - DisCharge_e;
		PreSoC_e = HistSoC_e[t];			//for next timestep
	}

	// Public output data, create private Battery object in parent
	year_TS HistSoC_e;
	year_TS HistCharg_e;
	year_TS HistDisch_e;
	year_TS HistAux_e;
	year_TS HistRTL_e;

private:
	const float Capacity_e;
	const float ChargMax_e;
	const float DischMax_e;
	const float RTLrate;
	const float AuxLoad_e;
	float PreSoC_e;
};
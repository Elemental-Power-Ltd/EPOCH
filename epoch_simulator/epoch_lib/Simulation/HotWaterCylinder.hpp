#include <cmath>

#include "TempSum.hpp"

class HotWaterCylinder {

public:
	// Constructor
	HotWaterCylinder(const HistoricalData& historicalData, const TaskData& taskData) :

		mCylinderVolume(taskData.DHW_cylinder_volume), // cylinder volume n litres
		mTimesteps(taskData.calculate_timesteps()),
		mTimestep_seconds(taskData.timestep_hours * 60 * 60),// set up timestep seconds in constructor
		mTimestep_hours(taskData.timestep_hours),
		mCapacity_h(calculate_Capacity_h()), // calculate tank energy capacity in constructor
		mDHW_discharging(historicalData.DHWdemand_data),
		mCylinderStartSoC_h(calculate_Capacity_h()), // set start SoC to full for now
		mDHW_charging(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),
		mDHW_shortfall_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),
		mDHW_standby_losses(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),
		mDHW_SoC_history(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),
		mDHW_ave_temperature(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),
		mDHW_diverter_load_e(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),
		mDHW_heat_pump_load_h(Eigen::VectorXf::Zero(taskData.calculate_timesteps())),
		mImport_tariff(historicalData.importtariff_data),
		mHeat_pump_power_h(taskData.ASHP_HPower) // will need to calculate energy per timestep
	{}

	// Calculate cylinder energy capacity based on T_setpoint, convert to kWh
	float calculate_Capacity_h() {
		mCapacity_h = (rho * mCylinderVolume * c_w * (T_setpoint - T_cold)) / 3600.0; // calculate kWh heat capacity
		return mCapacity_h;
	}

	void intialise_SoC() {
		mCylEnergy_h = mCylinderStartSoC_h; // set initial SoC to cylinder kWh heat capacity

		return;
	}

	void calculate_U() // Just in terms of volume for now, based on reference value of 1.7 W/C - 250 litre Valiant Unistor 1.42 kWh standing loss in 24 hours 
	{
		mU = 1.70 * pow((mCylinderVolume / 250), (2.0f / 3.0f));
		return;
	}


	// Update the model for one time step
	void update_SoC_basic(float E_charge_kWh, float V_draw_kWh, int timestep) {

		// Convert input charging energy from kWh to kJ
		float Charging_kjoules = E_charge_kWh * 3600.0; // kWh to kJ

		// Calculate energy lost due to draw-off
		float Discharging_kjoules = V_draw_kWh * 3600.0; // kWh to kJ

		// Update average temperature
		mT_ave = mCylEnergy_h * 3600.0 / (rho * mCylinderVolume * c_w) + T_cold;

		// Calculate standby energy losses (convert W to kW, then to kJ)
		float Standby_loss_kjoules = mU * (mT_ave - T_ambient) * (mTimestep_seconds) / 1000.0; // in kJ

		// Update stored energy
		mCylEnergy_h += (Charging_kjoules - Discharging_kjoules - Standby_loss_kjoules) / 3600.0; // convert back to kWh

		mDHW_standby_losses[timestep] = Standby_loss_kjoules / 3600.0; // record tank standby loss for reporting
		mDHW_ave_temperature[timestep] = mT_ave;

		//if (mCylEnergy_h < 0)
		//{
		//    mDHW_shortfall_e[timestep] = -mCylEnergy_h; // record shortfall in absolute terms
		//    mCylEnergy_h = 0;
		//}

		mDHW_SoC_history[timestep] = mCylEnergy_h;

		return;
	}

	void update_SoC_detailed(float E_charge_kWh, float V_draw_kWh)
	{
		//TBD this can will be the more detailed & computationally expensive cylinder model
		return;
	}

	void AllCalcs(TempSum& tempSum) {

		intialise_SoC();
		calculate_U();

		mAverage_tariff = mImport_tariff.mean(); // calculate average tariff as a threshold to charge

		update_SoC_basic(0, mDHW_discharging[0], 0);// initialise cylinder at timestep zero

		//mDHW_SoC_history[0] = mCylEnergy_h; // initialise state of charge

		for (int timestep = 1; timestep < mTimesteps; timestep++) // first timestep = 0 for C++ array
		{

			float timestep_charge = 0; // reference the State of charge to see available energy, report shortfall 
			// determine charge

			float max_charge_energy = mCapacity_h - getCylEnergy(); // assume tank can fully charge electrically in 1 timestep if need be
			float max_heat_pump_charge_energy = std::min((mCapacity_h - getCylEnergy()), (mHeat_pump_power_h * mTimestep_hours));


			float timestep_renewable_charge = 0; // this is by resitive immersion heating assume 1kWe = 1kWh
			float timestep_shortfall_charge = 0; // this is by restive immersion heating, electric shower or other instantaneous electric method assume 1kWe = 1kWh
			float timestep_lowtariff_charge = 0; // to charge from tariff schedule, this can be achieved by heat pump

			if (tempSum.Elec_e[timestep] < 0) // if there is a surplus of renewables, permit DHW charging by immersion and/or charge if there is a requirement for boost// must be after first timestep // can add tariff considertion later 
			{
				timestep_renewable_charge = std::min(-tempSum.Elec_e[timestep], max_charge_energy); // use renewable surplus as candidate amount to top up to tank capacit 
			}

			if (mImport_tariff[timestep] < mAverage_tariff)
			{
				timestep_lowtariff_charge = max_heat_pump_charge_energy - timestep_renewable_charge;
			}
			// if there will be insufficient total charge in this timestep to address current demand, top up to what is required and log this as shortfall
			if (mDHW_SoC_history[timestep - 1] + timestep_renewable_charge + timestep_lowtariff_charge < mDHW_discharging[timestep])

				// this is the minimum to support instantenous charging
			{
				timestep_shortfall_charge = std::min(max_charge_energy, (mDHW_discharging[timestep] - timestep_renewable_charge - timestep_lowtariff_charge - mDHW_SoC_history[timestep - 1]));
				mDHW_shortfall_e[timestep] = timestep_shortfall_charge;
			}

			timestep_charge = timestep_renewable_charge + timestep_lowtariff_charge + timestep_shortfall_charge;

			// need to determine heat pump DHW charging load vs immersion 
			update_SoC_basic(timestep_charge, mDHW_discharging[timestep], timestep); // apply charge & discharge to cylinder & calculate state 

			// log charge applied
			mDHW_charging[timestep] = timestep_charge; // total heat transfered to cylinder
			mDHW_diverter_load_e[timestep] = timestep_renewable_charge; // assume renewable energy divert is simple AC heater
			mDHW_heat_pump_load_h[timestep] = timestep_lowtariff_charge; // assume the low tariff charge is done by heat pump

		};

		// update tempSum to apply the electrical loads
		tempSum.Elec_e += mDHW_shortfall_e;
		tempSum.Elec_e += mDHW_diverter_load_e;

		tempSum.DHW_heatpump_ask_h += mDHW_heat_pump_load_h;

		return;

	}

	void Report(FullSimulationResult& result) {
		result.DHW_load = mDHW_discharging;
		result.DHW_charging = mDHW_charging;
		result.DHW_SoC = mDHW_SoC_history;
		result.DHW_Standby_loss = mDHW_standby_losses;
		result.DHW_ave_temperature = mDHW_ave_temperature;
		result.DHW_Shortfall = mDHW_shortfall_e;
	}

	// Get the current stored energy in the tank in kWh
	float getCylEnergy() const {
		return mCylEnergy_h;
	}

	year_TS getDHW_Charging() const {
		return mDHW_charging;
	}

	year_TS getDHW_shortfall() const {
		return mDHW_shortfall_e;
	}


private:

	float mCylinderVolume;
	const int mTimesteps;
	float mTimestep_seconds;
	float mTimestep_hours;


	const float c_w = 4.18;            // Specific heat capacity of water in kJ/kg·°C
	const float rho = 1.0;             // Density of water in kg/
	const float T_cold = 10.0;         // Cold water inlet temperature in °C
	const float T_ambient = 20.0;      // Ambient temperature in °C
	// 30 minutes in seconds
	const float T_setpoint = 55.0;     // Setpoint temperature for hot water in °C



	// State variables
	float mU;               // Heat loss coefficient in W/°C
	float mCapacity_h;         // heat capacity of tank in kWh
	float mCylEnergy_h;    // Stored heat energy in kWh
	float mT_ave;           // average water temperature in °C
	float mCylinderStartSoC_h; // starting state of charge in kWh

	float mHeat_pump_power_h; // max heat pump power

	float mAverage_tariff;

	year_TS mDHW_charging; // member timeseries for calculated charging
	year_TS mDHW_discharging;  // member timeseries for discharging from historical data
	year_TS mDHW_standby_losses;
	year_TS mDHW_shortfall_e;
	year_TS mDHW_SoC_history;
	year_TS mDHW_ave_temperature;
	year_TS mDHW_heat_pump_load_h;
	year_TS mDHW_diverter_load_e;
	year_TS mImport_tariff;

};


#include <cmath>

#include "../../TaskComponents.hpp"
#include "../../SiteData.hpp"
#include "../../TempSum.hpp"
#include "../../DayTariffStats.hpp"

class HotWaterCylinder {

public:
	// Constructor

	HotWaterCylinder(const SiteData& siteData, const DomesticHotWater& dhw, const HeatPumpData& heatPumpData, size_t tariff_index, const DayTariffStats& tariff_stats) :
		mCylinderVolume(dhw.cylinder_volume), // cylinder volume n litres
		mTimesteps(siteData.timesteps),
		mTimestep_seconds(std::chrono::duration<float>(siteData.timestep_interval_s).count()),// set up timestep seconds in constructor
		mTimestep_hours(siteData.timestep_hours),
		mCapacity_h(calculate_Capacity_h()), // calculate tank energy capacity in constructor
		mCylinderStartSoC_h(0.0), // set start SoC to empty; this will cause an initial charge but not give us free energy
		mHeat_pump_power_h(heatPumpData.heat_power), // will need to calculate energy per timestep
		mDHW_charging(Eigen::VectorXf::Zero(siteData.timesteps)),
		mDHW_discharging(siteData.dhw_demand),
		mDHW_standby_losses(Eigen::VectorXf::Zero(siteData.timesteps)),
		mDHW_local_shortfall(Eigen::VectorXf::Zero(siteData.timesteps)),
		mDHW_SoC_history(Eigen::VectorXf::Zero(siteData.timesteps)),
		mDHW_ave_temperature(Eigen::VectorXf::Zero(siteData.timesteps)),
		mDHW_heat_pump_load_h(Eigen::VectorXf::Zero(siteData.timesteps)),
		mDHW_diverter_load_e(Eigen::VectorXf::Zero(siteData.timesteps)),
		mImport_tariff(siteData.import_tariffs[tariff_index]),
		mTariffStats(tariff_stats)
	{}

	// Calculate cylinder energy capacity based on T_setpoint, convert to kWh
	float calculate_Capacity_h() {
		mCapacity_h = (rho * mCylinderVolume * c_w * (T_setpoint - T_cold)) / 3600.0f; // calculate kWh heat capacity
		return mCapacity_h;
	}

	void intialise_SoC() {
		mCylEnergy_h = mCylinderStartSoC_h; // set initial SoC to cylinder kWh heat capacity

		return;
	}

	void calculate_U() // Just in terms of volume for now, based on reference value of 1.7 W/C - 250 litre Valiant Unistor 1.42 kWh standing loss in 24 hours 
	{
		mU = 1.70f * pow((mCylinderVolume / 250), (2.0f / 3.0f));
		return;
	}


	// Update the model for one time step
	void update_SoC_basic(float E_charge_kWh, float V_draw_kWh, size_t timestep) {

		// Convert input charging energy from kWh to kJ
		float Charging_kjoules = E_charge_kWh * 3600.0f; // kWh to kJ

		// Calculate energy lost due to draw-off
		float Discharging_kjoules = V_draw_kWh * 3600.0f; // kWh to kJ

		// Update average temperature
		mT_ave = mCylEnergy_h * 3600.0f / (rho * mCylinderVolume * c_w) + T_cold;

		// Calculate standby energy losses (convert W to kW, then to kJ)
		// standby loss can be negative in rare circumstances (when the cylinder temperature is less than the ambient temperature)
		float Standby_loss_kjoules = mU * (mT_ave - T_ambient) * (mTimestep_seconds) / 1000.0f; // in kJ

		// Update stored energy
		mCylEnergy_h += (Charging_kjoules - Discharging_kjoules - Standby_loss_kjoules) / 3600.0f; // convert back to kWh

		// record tank standby loss for reporting
		mDHW_standby_losses[timestep] = Standby_loss_kjoules / 3600.0f;
		mDHW_ave_temperature[timestep] = mT_ave;

		if (mCylEnergy_h < 0)
		{
			// record shortfall in absolute terms
		    mDHW_local_shortfall[timestep] = -mCylEnergy_h;
		    mCylEnergy_h = 0;
		}

		mDHW_SoC_history[timestep] = mCylEnergy_h;

		return;
	}

	void update_SoC_detailed([[maybe_unused]] float E_charge_kWh, [[maybe_unused]] float V_draw_kWh)
	{
		//TBD this can will be the more detailed & computationally expensive cylinder model
		return;
	}

	void AllCalcs(TempSum& tempSum) {

		intialise_SoC();
		calculate_U();
		
		// initialise cylinder at timestep zero
		update_SoC_basic(0, mDHW_discharging[0], 0);

		// We start at t=1 here because we need to look at the previous timestep
		for (size_t timestep = 1; timestep < mTimesteps; timestep++) {

			float timestep_charge = 0;

			float dayAverage = mTariffStats.getDayAverage(timestep);
			float dayPercentile = mTariffStats.getDayPercentile(timestep);
			
			// determine charge
			float max_charge_energy = mCapacity_h - mCylEnergy_h;
			float max_heat_pump_charge_energy = std::min(max_charge_energy, (mHeat_pump_power_h * mTimestep_hours));


			float timestep_renewable_charge = 0; // this is by resitive immersion heating assume 1kWe = 1kWh
			float timestep_lowtariff_charge = 0; // to charge from tariff schedule, this can be achieved by heat pump

			if (tempSum.Elec_e[timestep] < 0) // if there is a surplus of renewables, permit DHW charging by immersion and/or charge if there is a requirement for boost// must be after first timestep // can add tariff considertion later 
			{
				timestep_renewable_charge = std::min(-tempSum.Elec_e[timestep], max_charge_energy); // use renewable surplus as candidate amount to top up to tank capacit 
			}

			// here we use <= dayAverage to ensure that we top up the DHW cylinder in scenarios with a fixed price tariffs
			if (mImport_tariff[timestep] <= dayAverage && mImport_tariff[timestep] <= dayPercentile) {
				timestep_lowtariff_charge = max_heat_pump_charge_energy - timestep_renewable_charge;
			}

			timestep_charge = timestep_renewable_charge + timestep_lowtariff_charge;

			update_SoC_basic(timestep_charge, mDHW_discharging[timestep], timestep);

			// total heat transfered to cylinder
			mDHW_charging[timestep] = timestep_charge;
			// assume renewable energy divert is simple AC heater
			mDHW_diverter_load_e[timestep] = timestep_renewable_charge;
			// assume the low tariff charge is done by heat pump
			mDHW_heat_pump_load_h[timestep] = timestep_lowtariff_charge;
		};

		// update tempSum to apply the electrical loads
		// 
		// we assume that any localised shortfall to the cylinder is met by immersion / resistive heating
		// so we transfer any 'shortfall' to the electrical load
		// crucially, this is not (yet?) a system-wide shortfall
		tempSum.Elec_e += mDHW_local_shortfall;
		tempSum.Elec_e += mDHW_diverter_load_e;

		tempSum.DHW_load_h = mDHW_heat_pump_load_h;

		return;

	}

	void Report(ReportData& reportData) {
		// TODO - we may need to report the actual discharging from the tank separately from the instantaneous demand
		//  (mDHW_discharging is just historicalData.DHWdemand_data)
		reportData.DHW_load = mDHW_discharging;
		reportData.DHW_charging = mDHW_charging;
		reportData.DHW_SoC = mDHW_SoC_history;
		reportData.DHW_Standby_loss = mDHW_standby_losses;
		reportData.DHW_ave_temperature = mDHW_ave_temperature;
		reportData.DHW_immersion_top_up = mDHW_local_shortfall;
		reportData.DHW_diverter_load = mDHW_diverter_load_e;
	}


private:

	float mCylinderVolume;
	const size_t mTimesteps;
	float mTimestep_seconds;
	float mTimestep_hours;

	const float c_w = 4.18f;            // Specific heat capacity of water in kJ/kg·°C
	const float rho = 1.0f;             // Density of water in kg/L
	const float T_cold = 10.0f;         // Cold water inlet temperature in °C
	const float T_ambient = 20.0f;      // Ambient temperature in °C
	const float T_setpoint = 60.0f;     // Setpoint temperature for hot water in °C

	// State variables
	float mU;                           // Heat loss coefficient in W/°C
	float mCapacity_h;                  // heat capacity of tank in kWh
	float mCylEnergy_h;                 // Stored heat energy in kWh
	float mT_ave;                       // average water temperature in °C
	float mCylinderStartSoC_h;          // starting state of charge in kWh

	float mHeat_pump_power_h;           // max heat pump power

	year_TS mDHW_charging;              // member timeseries for calculated charging
	year_TS mDHW_discharging;           // member timeseries for discharging from historical data
	year_TS mDHW_standby_losses;
	year_TS mDHW_local_shortfall;
	year_TS mDHW_SoC_history;
	year_TS mDHW_ave_temperature;
	year_TS mDHW_heat_pump_load_h;
	year_TS mDHW_diverter_load_e;
	year_TS mImport_tariff;

	const DayTariffStats& mTariffStats;

};


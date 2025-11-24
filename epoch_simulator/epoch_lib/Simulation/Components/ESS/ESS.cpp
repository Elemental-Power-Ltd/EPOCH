#include "ESS.hpp"


BasicESS::BasicESS(const SiteData& siteData, const EnergyStorageSystem& essData, size_t tariff_index, const DayTariffStats& tariff_stats) :
    ESS(siteData),
    mBattery(siteData, essData),
    mESS_mode(essData.battery_mode),
    mTimesteps(siteData.timesteps),
    mThresholdSoC(essData.capacity * 0.5f),
    mEnergyCalc(0.0f),
    mImport_tariff(siteData.import_tariffs[tariff_index]),
    mTariffStats(tariff_stats)
{
}

void BasicESS::StepCalc(TempSum& tempSum, const float futureEnergy_e, const size_t t)
{
    // mESS_mode Consume = 1, Resilient = 2, Threshold = 3, Price = 4, Carbon = 5
    switch (mESS_mode) {
    case BatteryMode::CONSUME: // Consume mode
        if (tempSum.Elec_e[t] >= 0) {  // Surplus Demand, discharge ESS
            mEnergyCalc = std::min(tempSum.Elec_e[t], mBattery.getAvailableDischarge());
            mBattery.doDischarge(mEnergyCalc, t);
            tempSum.Elec_e[t] = tempSum.Elec_e[t] - mEnergyCalc;
        }
        else {        // Surplus Generation, charge ESS
            mEnergyCalc = std::min(-tempSum.Elec_e[t], mBattery.getAvailableCharge());
            mBattery.doCharge(mEnergyCalc, t);
            tempSum.Elec_e[t] = tempSum.Elec_e[t] + mEnergyCalc;
        }
        break;
    case BatteryMode::CONSUME_PLUS:
        float averageTariff = mTariffStats.getDayAverage(t);
        float percentileTariff = mTariffStats.getDayPercentile(t);
        
        // if we satisfy top-up conditions in this timestep, only do this charge. 75% is the threshold SoC level
        if(mImport_tariff[t] < averageTariff && 
            mImport_tariff[t] <= percentileTariff && 
            mBattery.GetSoC()/mBattery.GetCapacity_e() < 0.75f) {

            // calculate how much energy we want to put into the battery
            mEnergyCalc = std::min((mBattery.GetCapacity_e()*0.75f), mBattery.getAvailableCharge());
            // cap by the amount of energy available to us
            mEnergyCalc = std::min(mEnergyCalc, futureEnergy_e - tempSum.Elec_e[t]);
            mBattery.doCharge(mEnergyCalc, t);
            tempSum.Elec_e[t] = tempSum.Elec_e[t] + mEnergyCalc;
        }
        else if (tempSum.Elec_e[t] >= 0) {  // Surplus Demand, discharge ESS
            mEnergyCalc = std::min(tempSum.Elec_e[t], mBattery.getAvailableDischarge());
            mBattery.doDischarge(mEnergyCalc, t);
            tempSum.Elec_e[t] = tempSum.Elec_e[t] - mEnergyCalc;
        }
        else {        // Surplus Generation, charge ESS
            mEnergyCalc = std::min(-tempSum.Elec_e[t], mBattery.getAvailableCharge());
            mBattery.doCharge(mEnergyCalc, t);
            tempSum.Elec_e[t] = tempSum.Elec_e[t] + mEnergyCalc;
        }
        break;
    }
    // FIXME JW - reintroduce the other modes incrementally

    //case 3: // Threshold mode
    //    if (mBattery.GetSoC() > mThresholdSoC) {   // High SoC = Consume mode (1)
    //        if (tempSum.Elec_e[t] >= 0) {   // Surplus Demand, discharge ESS
    //            mEnergyCalc = std::min(tempSum.Elec_e[t], mBattery.getAvailableDischarge());
    //            mBattery.doDischarge(mEnergyCalc, t);
    //            tempSum.Elec_e[t] = tempSum.Elec_e[t] - mEnergyCalc;
    //        }
    //        else {            // Surplus Generation, charge ESS
    //            mEnergyCalc = std::min(-tempSum.Elec_e[t], mBattery.getAvailableCharge());
    //            mBattery.doCharge(mEnergyCalc, t);
    //            tempSum.Elec_e[t] = tempSum.Elec_e[t] + mEnergyCalc;
    //        }
    //    }
    //    else {                              // Low SoC = Resilient Mode	
    //        if ((tempSum.Elec_e[t] - AvailGridImp) >= 0) {		// Grid cannot meet Demand, discharge ESS		
    //            mEnergyCalc = std::min((tempSum.Elec_e[t] - AvailGridImp), mBattery.getAvailableDischarge());
    //            mBattery.doDischarge(mEnergyCalc, t);
    //            tempSum.Elec_e[t] = tempSum.Elec_e[t] - mEnergyCalc;
    //        }
    //        else {  // Charge ESS from Grid headroom or surplus Generation		
    //            mEnergyCalc = std::min(-(tempSum.Elec_e[t] - AvailGridImp), mBattery.getAvailableCharge());
    //            mBattery.doCharge(mEnergyCalc, t);
    //            tempSum.Elec_e[t] = tempSum.Elec_e[t] + mEnergyCalc;
    //        }
    //    }
    //    break;

    //case 4: // Price minimisation mode
    //    // placeholder for lookahead supplier price mode
    //    // v0-7 lookahead case = dynamic based on volume forecast, omit for now
    //    break;

    //case 5: // Carbon minimisation mode
    //    // placholder for lookahead grid carbon mode
    //    break;

    //default: // Resilient Mode case should be default							
    //    if ((tempSum.Elec_e[t] - AvailGridImp) >= 0) {		// Grid cannot meet Demand, discharge ESS		
    //        mEnergyCalc = std::min((tempSum.Elec_e[t] - AvailGridImp), mBattery.getAvailableDischarge());
    //        mBattery.doDischarge(mEnergyCalc, t);
    //        tempSum.Elec_e[t] = tempSum.Elec_e[t] - mEnergyCalc;
    //    }
    //    else {  // Charge ESS from Grid headroom or surplus Generation		
    //        mEnergyCalc = std::min(-(tempSum.Elec_e[t] - AvailGridImp), mBattery.getAvailableCharge());
    //        mBattery.doCharge(mEnergyCalc, t);
    //        tempSum.Elec_e[t] = tempSum.Elec_e[t] + mEnergyCalc;
    //    }
    //}

}

float BasicESS::AvailDisch()
{
	return mBattery.getAvailableDischarge();
}

void BasicESS::Report(ReportData& reportData) const
{
    reportData.ESS_charge = mBattery.mHistCharg_e;
    reportData.ESS_discharge = mBattery.mHistDisch_e;
    reportData.ESS_resulting_SoC = mBattery.mHistSoC_e;

    // TODO - make a report method in the battery and call that instead
    reportData.ESS_AuxLoad = mBattery.mHistAux_e;
    reportData.ESS_RTL = mBattery.mHistRTL_e;
}


NullESS::NullESS(const SiteData& siteData) 
    : ESS(siteData)
{
}

void NullESS::StepCalc([[maybe_unused]] TempSum& tempSum, [[maybe_unused]] const float futureEnergy_e, [[maybe_unused]] const size_t t)
{
    // Do nothing
}

float NullESS::AvailDisch()
{
    // Null ESS returns 0 available charge
    return 0.0f;
}

void NullESS::Report([[maybe_unused]] ReportData& reportData) const
{
    // Do nothing
}

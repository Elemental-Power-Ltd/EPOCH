#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>
#include <algorithm>

#include "../../TaskComponents.hpp"
#include "../../SiteData.hpp"
#include "../../../Definitions.hpp"
#include "../../TempSum.hpp"
#include "Battery.hpp"

class ESS {
public:
    ESS(const SiteData& siteData) {};
    virtual ~ESS() = default;

    virtual void StepCalc(TempSum& tempSum, const float futureEnergy_e, const size_t t) = 0;
    virtual float AvailDisch() = 0;
    virtual void Report(ReportData& reportData) const = 0;
};


class BasicESS : public ESS {
public:
    BasicESS(const SiteData& siteData, const EnergyStorageSystem& essData);

    void StepCalc(TempSum& tempSum, const float futureEnergy_e, const size_t t);
    float AvailDisch();
    void Report(ReportData& reportData) const;

private:
    Battery mBattery;
    const BatteryMode mESS_mode;
    const size_t mTimesteps;
    const float mThresholdSoC;

    float mEnergyCalc;
};


// This is a crude workaround for the fact that the current balancing loop always assumes there is a battery
// The methods do nothing and return 0 so it appears to the code as if there is an unusable battery present
class NullESS : public ESS {
public:
    NullESS(const SiteData& siteData);

    void StepCalc(TempSum& tempSum, const float futureEnergy_e, const size_t t);
    float AvailDisch();
    void Report(ReportData& reportData) const;
};


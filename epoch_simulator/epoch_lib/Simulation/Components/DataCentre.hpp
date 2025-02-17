#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "../ASHP.hpp"
#include "../TempSum.hpp"
#include "../SiteData.hpp"
#include "../TaskComponents.hpp"
#include "../../Definitions.hpp"

enum class DataCentreOptimisationMode { Target, Price, Carbon };
constexpr float SCALAR_HEAT_YIELD = 0.75f;

class DataCentre {

public:
    DataCentre(const SiteData& siteData) {};
    virtual ~DataCentre() = default;

    virtual void AllCalcs(TempSum& tempSum) = 0;
    virtual void StepCalc(TempSum& tempSum, const float futureEnergy_e, const size_t t) = 0;
    virtual float getTargetLoad(size_t timestep) = 0;
    virtual void Report(ReportData& reportData) const = 0;
};


class BasicDataCentre : public DataCentre {
public:
    BasicDataCentre(const SiteData& siteData, const DataCentreData& dc);

    void AllCalcs(TempSum& tempSum);
    void StepCalc(TempSum& tempSum, const float futureEnergy_e, const size_t t);
    float getTargetLoad(size_t timestep);
    void Report(ReportData& reportData) const;

private:
    const size_t mTimesteps;
    const int mOptimisationMode;
    const float mDataCentreMaxLoad_e;

    year_TS mTargetLoad_e;
    year_TS mActualLoad_e;
};


class DataCentreWithASHP : public DataCentre {
public:
    DataCentreWithASHP(const SiteData& siteData, const DataCentreData& dc, const HeatPumpData& hp);

    void AllCalcs(TempSum& tempSum);
    void StepCalc(TempSum& tempSum, const float futureEnergy_e, const size_t t);
    float getTargetLoad(size_t timestep);
    void Report(ReportData& reportData) const;

private:
    HotRoomHeatPump mHeatPump;

    const size_t mTimesteps;
    const DataCentreOptimisationMode mOptimisationMode;
    const float mDataCentreMaxLoad_e;
    const float mHeatScalar;

    year_TS mTargetLoad_e;
    year_TS mActualLoad_e;
    year_TS mAvailableHotHeat_h;
    year_TS mTargetHeat_h;
};







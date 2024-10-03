#pragma once

#include <Eigen/Core>
#include <Eigen/Dense>

#include "../ASHP.hpp"
#include "../TempSum.hpp"
#include "../TaskData.hpp"
#include "../../Definitions.hpp"

enum class DataCentreOptimisationMode { Target, Price, Carbon };

class DataCentre {

public:
    DataCentre(const HistoricalData& historicalData, const TaskData& taskData) {};
    virtual ~DataCentre() = default;

    virtual void AllCalcs(TempSum& tempSum) = 0;
    virtual void StepCalc(TempSum& tempSum, const float futureEnergy_e, const int t) = 0;
    virtual float getTargetLoad(int timestep) = 0;
    virtual void Report(FullSimulationResult& result) const = 0;
};


class BasicDataCentre : public DataCentre {
public:
    BasicDataCentre(const HistoricalData& historicalData, const TaskData& taskData);

    void AllCalcs(TempSum& tempSum);
    void StepCalc(TempSum& tempSum, const float futureEnergy_e, const int t);
    float getTargetLoad(int timestep);
    void Report(FullSimulationResult& result) const;

private:
    const int mTimesteps;
    const int mOptimisationMode;
    const float mDataCentreMaxLoad_e;

    year_TS mTargetLoad_e;
    year_TS mActualLoad_e;
};


class DataCentreWithASHP : public DataCentre {
public:
    DataCentreWithASHP(const HistoricalData& historicalData, const TaskData& taskData);

    void AllCalcs(TempSum& tempSum);
    void StepCalc(TempSum& tempSum, const float futureEnergy_e, const int t);
    float getTargetLoad(int timestep);
    void Report(FullSimulationResult& result) const;

private:
    HotRoomHeatPump mHeatPump;

    const int mTimesteps;
    const DataCentreOptimisationMode mOptimisationMode;
    const float mDataCentreMaxLoad_e;
    const float mHeatScalar;

    year_TS mTargetLoad_e;
    year_TS mActualLoad_e;
    year_TS mAvailableHotHeat_h;
    year_TS mTargetHeat_h;
};







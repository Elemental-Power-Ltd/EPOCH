#pragma once

#include "TaskData.hpp"
#include "../Definitions.hpp"

// For the demo, always use the weather compensation mode in column 2
// We look this is up by passing 2 as the sendTemp
// (this is not 2 degrees, the table is hacked to include some compensation modes)
const float FIXED_SEND_TEMP_VAL = 2;

struct HeatpumpValues {
    float Heat_h;
    float Load_e;
};

class ASHPLookup
{
public:
    ASHPLookup(const HistoricalData& historicalData, const TaskData& taskData, float sendTemperature);

    float MaxElecLoad() const;

    HeatpumpValues Lookup(float airTemp);

private:

    void precomputeLookupTable(const HistoricalData& historicalData, const TaskData& taskData, float sendTemp);

    float computeInput(const HistoricalData& historicalData, float sendTemp, float airTemp) const;
    float computeOutput(const HistoricalData& historicalData, float sendTemp, float airTemp) const;

    int airTempToRowIndex(const HistoricalData& historicalData, float airTemp) const;
    int sendTempToColIndex(const HistoricalData& historicalData, float sendTemp) const;

    float mMaxLoad_e;

    std::vector<float> mInputByDegree;
    std::vector<float> mOutputByDegree;

    // the minimum and maximum temperature values we have data for
    int mMinAirTemp;
    int mMaxAirTemp;

    // offset to translate a temperature in degrees to an index in the lookup vectors
    // e.g. if the offset is 15 0deg will be stored in the 15th position
    int mOffset;

};

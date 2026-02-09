#include "ASHPLookup.hpp"

ASHPLookup::ASHPLookup(const SiteData& siteData, const HeatPumpData& hp, float sendTemperature)
{
    precomputeLookupTable(siteData, hp, sendTemperature);
}


// Lookup the CoP values for the given temperature
// This could either be the ambient air temperature or a hotroom air temperature
HeatpumpValues ASHPLookup::Lookup(float supplyTemp) {

    // much faster than std::round
    int supplyTempDeg = static_cast<int>(supplyTemp + (supplyTemp >= 0 ? 0.5f : -0.5f));;

    if (supplyTempDeg < mMinAirTemp) {
        return HeatpumpValues{ mOutputByDegree[0], mInputByDegree[0] };
    }
    else if (supplyTempDeg > mMaxAirTemp) {
        return HeatpumpValues{
            mOutputByDegree[mOutputByDegree.size() - 1],
            mInputByDegree[mInputByDegree.size() - 1]
        };
    }

    return HeatpumpValues{ mOutputByDegree[supplyTempDeg + mOffset], mInputByDegree[supplyTempDeg + mOffset] };
}

void ASHPLookup::precomputeLookupTable(const SiteData& siteData, const HeatPumpData& hp, float sendTemp) {
    mMinAirTemp = static_cast<int>(std::floor(siteData.ashp_input_table(1, 0)));
    mMaxAirTemp = static_cast<int>(std::ceil(siteData.ashp_input_table(siteData.ashp_input_table.rows() - 1, 0)));

    mOffset = -1 * mMinAirTemp;

    // The reference table is assumed to be for a 1KW heatpump
    // We scale the values by the modelled ASHP Power per timestep
    float powerScalar = hp.heat_power * siteData.timestep_hours;

    for (int airTempByDegree = mMinAirTemp; airTempByDegree <= mMaxAirTemp; airTempByDegree++) {
        float airTemp = static_cast<float>(airTempByDegree);

        float scaledInput = computeInput(siteData, sendTemp, airTemp) * powerScalar;
        mInputByDegree.emplace_back(scaledInput);

        float scaledOutput = computeOutput(siteData, sendTemp, airTemp) * powerScalar;
        mOutputByDegree.emplace_back(scaledOutput);
    }
}


float ASHPLookup::computeInput(const SiteData& siteData, float sendTemp, float airTemp) const
{
    int col = sendTempToColIndex(siteData, sendTemp);
    int row = airTempToRowIndex(siteData, airTemp);

    float input = siteData.ashp_input_table(row, col);
    return input;
}

float ASHPLookup::computeOutput(const SiteData& siteData, float sendTemp, float airTemp) const
{
    int col = sendTempToColIndex(siteData, sendTemp);
    int row = airTempToRowIndex(siteData, airTemp);

    float output = siteData.ashp_output_table(row, col);
    return output;
}

// Determine the Row index of the table to use for lookups, given a air temp
// This 'snaps back' to the closest value lower than it in the table
// i.e. the last row that does not exceed the given air temp
int ASHPLookup::airTempToRowIndex(const SiteData& siteData, float airTemp) const
{
    int num_rows = static_cast<int>(siteData.ashp_input_table.rows());

    if (airTemp < siteData.ashp_input_table(1, 0)) {
        // default to the lowest possible value
        return 1;
    }

    // start at 1, 0 is header
    for (int row = 1; row < num_rows; row++) {
        if (siteData.ashp_input_table(row, 0) > airTemp) {
            // this column exceeds the air temp, return the previous column
            return row - 1;
        }
    }

    // no value in the table reaches this air temp
    // use the highest (last) temperature we can
    return num_rows - 1;
}

// Determine the Column index of the table to use for lookups, given a send temp
// This 'snaps back' to the closest value lower than it in the table
// i.e. the last column that does not exceed the given send temp
int ASHPLookup::sendTempToColIndex(const SiteData& siteData, float sendTemp) const
{
    int num_cols = static_cast<int>(siteData.ashp_input_table.cols());

    if (sendTemp < siteData.ashp_input_table(0, 1)) {
        // default to the first column
        return 1;
    }

    // start at 1, 0 is header
    for (int col = 1; col < num_cols; col++) {
        if (siteData.ashp_input_table(0, col) > sendTemp) {
            // this column exceeds the sendTemp, return the previous column
            return col - 1;
        }
    }

    // no value in the table reaches this send temp
    // use the highest (last) temperature we can
    return num_cols - 1;
}

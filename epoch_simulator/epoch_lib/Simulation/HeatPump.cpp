#include "HeatPump.hpp"

#include <cmath>


HeatPump::HeatPump(const HistoricalData& historicalData, const TaskData& taskData):
	// ASHP_HSource of 1 corresponds to ambient air, 2 corresponds to hotroom
	mHeatSource(taskData.ASHP_HSource == 1 ? HeatSource::AMBIENT_AIR : HeatSource::HOTROOM),
	mRadTemp(taskData.ASHP_RadTemp),
	mFlexLoadMax(taskData.Flex_load_max),
	mHYield(taskData.ScalarHYield)
{
	// we need to calculate the ambient air values irrespective of the heat source
	precomputeAmbientAirValues(historicalData, taskData);

	if (mHeatSource == HeatSource::HOTROOM) {
		precomputeHotroomValues(historicalData, taskData);
	}
}

float HeatPump::getAmbientInput(float airTemp) const
{
	int airTempDeg = std::round(airTemp);

	if (airTempDeg < mMinAirTemp) {
		return mInputByDegree[0];
	}
	else if (airTempDeg > mMaxAirTemp) {
		return mInputByDegree[mInputByDegree.size() - 1];
	}

	return mInputByDegree[airTempDeg + mOffset];
}

float HeatPump::getHotroomInput() const
{
	return mHotroomInput;
}

float HeatPump::getAmbientOutput(float airTemp) const
{
	int airTempDeg = std::round(airTemp);

	if (airTempDeg < mMinAirTemp) {
		return mOutputByDegree[0];
	}
	else if (airTempDeg > mMaxAirTemp) {
		return mOutputByDegree[mOutputByDegree.size() - 1];
	}

	return mOutputByDegree[airTempDeg + mOffset];
}

float HeatPump::getOutput(float airTemp) const
{
	float ambientOutput = getAmbientOutput(airTemp);

	switch (mHeatSource) {
	case HeatSource::AMBIENT_AIR :
		return ambientOutput;
	case HeatSource::HOTROOM :
		return std::min(mHotroomOutput, ambientOutput + mFlexLoadMax * mHYield);
	default:
		throw std::exception();
	}
}

HeatSource HeatPump::getHeatSource() const
{
	return mHeatSource;
}


void HeatPump::precomputeAmbientAirValues(const HistoricalData& historicalData, const TaskData& taskData)
{
	mMinAirTemp = std::floor(historicalData.ASHPinputtable[0][1]);
	mMaxAirTemp = std::ceil(historicalData.ASHPinputtable[0][historicalData.ASHPinputtable[0].size() - 1]);

	mOffset = -1 * mMinAirTemp;

	// We scale all of the values by the modelled HP power and descale by the reference model power
	float powerRatio = taskData.ASHP_HPower / mReferencePower;

	for (int airTemp = mMinAirTemp; airTemp <= mMaxAirTemp; airTemp++) {
		float scaledInput = computeInput(historicalData, mRadTemp, airTemp) * powerRatio;
		mInputByDegree.emplace_back(scaledInput);

		float scaledOutput = computeOutput(historicalData, mRadTemp, airTemp) * powerRatio;
		mOutputByDegree.emplace_back(scaledOutput);
	}
}

void HeatPump::precomputeHotroomValues(const HistoricalData& historicalData, const TaskData& taskData)
{
	// We scale all of the values by the modelled HP power and descale by the reference model power
	float powerRatio = taskData.ASHP_HPower / mReferencePower;

	mHotroomInput = computeInput(historicalData, taskData.ASHP_RadTemp, taskData.ASHP_HotTemp) * powerRatio;
	mHotroomOutput = computeOutput(historicalData, taskData.ASHP_RadTemp, taskData.ASHP_HotTemp) * powerRatio;
}

float HeatPump::computeInput(const HistoricalData& historicalData, float radTemp, float airTemp) const
{
	int col = radTempToColIndex(historicalData, radTemp);
	int row = airTempToRowIndex(historicalData, airTemp);

	float input = historicalData.ASHPinputtable[col][row];
	return input;
}

float HeatPump::computeOutput(const HistoricalData& historicalData, float radTemp, float airTemp) const
{
	int col = radTempToColIndex(historicalData, radTemp);
	int row = airTempToRowIndex(historicalData, airTemp);

	float output = historicalData.ASHPoutputtable[col][row];
	return output;
}

// Determine the Column index of the table to use for lookups, given a rad temp
// This 'snaps back' to the closest value lower than it in the table
// i.e. the last column that does not exceed the given rad temp
int HeatPump::radTempToColIndex(const HistoricalData& historicalData, float radTemp) const
{
	int num_cols = historicalData.ASHPinputtable.size();

	if (radTemp < historicalData.ASHPinputtable[1][0]) {
		// default to the first column
		return 1;
	}

	// start at 1, 0 is header
	for (int col = 1; col < num_cols; col++) {
		if (historicalData.ASHPinputtable[col][0] > radTemp) {
			// this column exceeds the radTemp, return the previous column
			return col - 1;
		}
	}

	// no value in the table reaches this rad temp
	// use the highest (last) temperature we can
	return num_cols - 1;
}

// Determine the Row index of the table to use for lookups, given a air temp
// This 'snaps back' to the closest value lower than it in the table
// i.e. the last row that does not exceed the given air temp
int HeatPump::airTempToRowIndex(const HistoricalData& historicalData, float airTemp) const
{
	int num_rows = historicalData.ASHPinputtable[0].size();

	if (airTemp < historicalData.ASHPinputtable[0][1]) {
		// default to the lowest possible value
		return 1;
	}

	// start at 1, 0 is header
	for (int row = 1; row < num_rows; row++) {
		if (historicalData.ASHPinputtable[0][row] > airTemp) {
			// this column exceeds the air temp, return the previous column
			return row - 1;
		}
	}

	// no value in the table reaches this air temp
	// use the highest (last) temperature we can
	return num_rows - 1;
}

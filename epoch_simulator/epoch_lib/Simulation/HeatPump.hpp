#include "../Definitions.hpp"

/**
* This class contains the internal logic for performing heatpump performance lookups
* We precompute the results over a range of temperatures to give a quick lookup during the time-critical loops
* This lookup is discretised to the nearest degree celsius
*/

enum class HeatSource {
	AMBIENT_AIR,
	HOTROOM
};

class HeatPump {
public:
	HeatPump(const HistoricalData& historicalData, const TaskData& taskData);

	float getAmbientInput(float airTemp) const;
	float getHotroomInput() const;
	float getOutput(float airTemp) const;

	HeatSource getHeatSource() const;


private:
	float getAmbientOutput(float airTemp) const;

	void precomputeAmbientAirValues(const HistoricalData& historicalData, const TaskData& taskData);
	void precomputeHotroomValues(const HistoricalData& historicalData, const TaskData& taskData);

	float computeInput(const HistoricalData& historicalData, float radTemp, float airTemp) const;
	float computeOutput(const HistoricalData& historicalData, float radTemp, float airTemp) const;

	int radTempToColIndex(const HistoricalData& historicalData, float radTemp) const;
	int airTempToRowIndex(const HistoricalData& historicalData, float airTemp) const;


	// per degree values for the ambient air
	std::vector<float> mInputByDegree;
	std::vector<float> mOutputByDegree;

	// constant values for the hotroom
	float mHotroomInput;
	float mHotroomOutput;

	// the minimum and maximum temperature values we have data for
	int mMinAirTemp;
	int mMaxAirTemp;
	// offset to translate a temperature in degrees to an index in one of the lookup vectors
	// e.g. if the offset is 15, 0deg will be stored in the 15th position
	int mOffset;

	// the reference heating power for the ASHP lookup, based on SAMSUNG AE140BXYDGG/EU 14 kWtherm
	const float mReferencePower = 14.0f;
	
	const float mRadTemp;
	const HeatSource mHeatSource;
	const float mFlexLoadMax;
	const float mHYield;

};
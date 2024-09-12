#pragma once

class ASHPperf_cl
{
public:
	ASHPperf_cl(const HistoricalData& historicalData, const ASHPData_st& ASHPData) :
		// FUDGED WITH FIXED VALUES
		// UNFUDGE: Initilaise lookup tables using historicalData.ASHPinputtable .ASHPoutputtable
		MaxLoad_e(ASHPData.PowerScalar * 0.5f),
		MaxHeat_h(ASHPData.PowerScalar * 2.0f)
	{}

	float MaxElecLoad() const {
		return MaxLoad_e;
	}

	void Lookup(const float TargetHeat_h, ASHP_HE_st& ASHPoutputs) {
		// FUDGE: Needs to convert TargetHeat_h to int and lookup in perf tables
		ASHPoutputs.Heat_h = MaxHeat_h;
		ASHPoutputs.Load_e = MaxLoad_e;
	}

private:
	// Lookup arrays: Index Input temp, output max Heat & max electricity
	const float MaxLoad_e;
	const float MaxHeat_h;
};
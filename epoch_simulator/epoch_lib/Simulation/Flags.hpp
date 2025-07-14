#pragma once

#include "TaskData.hpp"


enum class EVFlag { NOT_PRESENT, NON_BALANCING, BALANCING };
enum class DataCentreFlag {NOT_PRESENT, NON_BALANCING, BALANCING };

class Flags
{
public:
	Flags(const TaskData& taskData)
	{
		if (taskData.electric_vehicles) {
			if (taskData.electric_vehicles->flexible_load_ratio > 0) {
				mEVConfiguration = EVFlag::BALANCING;
			}
			else {
				mEVConfiguration = EVFlag::NON_BALANCING;
			}
		}
		else {
			mEVConfiguration = EVFlag::NOT_PRESENT;
		}


		// With the current configuration, there is no way to specify that there is a Data Centre but it is non-balancing
		if (taskData.data_centre) {
			mDataCentreConfiguration = DataCentreFlag::BALANCING;
		}
		else {
			mDataCentreConfiguration = DataCentreFlag::NOT_PRESENT;
		}
	}

	EVFlag getEVFlag() {
		return mEVConfiguration;
	}

	DataCentreFlag getDataCentreFlag() {
		return mDataCentreConfiguration;
	}

	bool dataCentrePresent() {
		return mDataCentreConfiguration == DataCentreFlag::BALANCING || mDataCentreConfiguration == DataCentreFlag::NON_BALANCING;
	}

	bool EVPresent() {
		return mEVConfiguration == EVFlag::BALANCING || mEVConfiguration == EVFlag::NON_BALANCING;
	}


private:

	EVFlag mEVConfiguration;
	DataCentreFlag mDataCentreConfiguration;
};
#pragma once

#include "TaskData.hpp"


enum class EVFlag { NOT_PRESENT, NON_BALANCING, BALANCING };
enum class DataCentreFlag {NOT_PRESENT, NON_BALANCING, BALANCING };

class Config
{
public:
	Config(const TaskData& taskData)
	{
		// Check TaskData for component presence (to avoid creating and running empty components)
		if ((taskData.s7_EV_CP_number + taskData.f22_EV_CP_number + taskData.r50_EV_CP_number + taskData.u150_EV_CP_number) > 0) {

			if (taskData.EV_flex > 0) {
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
		if (taskData.Flex_load_max > 0) {
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
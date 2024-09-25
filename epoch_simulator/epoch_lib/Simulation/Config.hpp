#pragma once

#include "TaskData.hpp"

class Config
{
public:
	Config(const TaskData& taskData) :
		// Flags determine whether to create an energy component, initialise to 'not present' (=0)
		EV1flag(0),
		DataCflag(0),
		// Flags determine whether to call an energy component 'in loop' for balancing, initialise to 'not balancing' (=0)
		EV1balancing(0),
		DataCbalancing(0)
	{
		// Check TaskData for component presence (to avoid creating and running empty components)
		if ((taskData.s7_EV_CP_number + taskData.f22_EV_CP_number + taskData.r50_EV_CP_number + taskData.u150_EV_CP_number) > 0) {
			// At least 1 EV_CP
			EV1flag = 1;
			EV1balancing = 1;
		}
		if (taskData.Flex_load_max > 0) {
			// There is a DataC
			DataCflag = 1;
			DataCbalancing = 1;
		}
		if (taskData.EV_flex > 0) {
			// EV charging is flexible (2)
			EV1balancing = 2;
		}
		if (taskData.Flex_load_max > 0) {
			// FUTURE: Seperate DataC load from its flex status (2)
			DataCbalancing = 2;
		}
		// if(taskData.ScalarRG1 + taskData.ScalarRG2 + taskData.ScalarRG3 + taskData.ScalarRG4) > 0) {PV1flag = 1;}
		// could also test PV hist data > 0
		// if(std:min(taskData.ESS_charge_power, taskData.ESS_discharge_power, taskData.ESS_capacity) > 0) {ESSflag = 1;}
	}

	int DataC() {
		return DataCflag;
	}
	int EV1() {
		return EV1flag;
	}
	int EV1bal() {
		return EV1balancing;
	}
	int DataCbal() {
		return DataCbalancing;
	}

private:
	int EV1flag;
	int DataCflag;
	int EV1balancing;
	int DataCbalancing;
};
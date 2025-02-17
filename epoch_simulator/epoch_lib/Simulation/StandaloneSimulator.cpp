#include "StandaloneSimulator.hpp"

#include "../io/FileHandling.hpp"

StandaloneSimualtor::StandaloneSimualtor() :
	mFileConfig{"./InputData", "./OutputData", "./Config"},
	mSiteData{ readSiteData(mFileConfig)},
	mSimulator{}
{
}

SimulationResult StandaloneSimualtor::simulateScenario(const TaskData& taskData, bool fullReporting)
{
	SimulationType simulationType = fullReporting 
		? SimulationType::FullReporting 
		: SimulationType::ResultOnly;

	return mSimulator.simulateScenario(mSiteData, taskData, simulationType);
}

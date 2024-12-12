#include "StandaloneSimulator.hpp"

#include "../io/FileHandling.hpp"

StandaloneSimualtor::StandaloneSimualtor() :
	mFileConfig{"./InputData", "./OutputData", "./Config"},
	mHistoricalData{ readHistoricalData(mFileConfig)},
	mSimulator{}
{
}

SimulationResult StandaloneSimualtor::simulateScenario(const TaskData& taskData, bool fullReporting)
{
	SimulationType simulationType = fullReporting 
		? SimulationType::FullReporting 
		: SimulationType::ResultOnly;

	return mSimulator.simulateScenario(mHistoricalData, taskData, simulationType);
}

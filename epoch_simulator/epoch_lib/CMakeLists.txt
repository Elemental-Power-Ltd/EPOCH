add_library(Epoch_lib STATIC
	"Definitions.hpp"
	"io/FileConfig.hpp"
	"io/FileHandling.cpp"
	"io/FileHandling.hpp"
	"io/EnumToString.cpp"
	"io/EnumToString.hpp"
	"io/TaskConfigJson.cpp"
	"io/TaskDataJson.cpp"
	"io/ToString.hpp"
	"io/ToString.cpp"

	"Optimisation/LeagueTable.cpp"
	"Optimisation/LeagueTable.hpp"
	"Optimisation/Optimiser.cpp"
	"Optimisation/Optimiser.hpp"
	"Optimisation/TaskGenerator.cpp"
	"Optimisation/TaskGenerator.hpp"
	
	"Simulation/Simulate.hpp"
	"Simulation/Simulate.cpp"
	"io/EpochConfig.cpp"
	"io/EpochConfig.hpp"
	"io/BufferedCSVWriter.cpp"
	"io/BufferedCSVWriter.hpp"
	"io/TaskDataJson.hpp"
	"io/SiteDataJson.hpp"
	"io/SiteDataJson.cpp"

	"Simulation/ASHP.hpp"
	"Simulation/ASHPambient.hpp"
	"Simulation/ASHPLookup.hpp"
	"Simulation/ASHPLookup.cpp"
	"Simulation/Components/ESS/Battery.hpp"
	"Simulation/Components/ESS/ESS.cpp"
	"Simulation/Components/ESS/ESS.hpp"
	"Simulation/EV.hpp"
	"Simulation/Flags.hpp"
	"Simulation/GasCH.hpp"
	"Simulation/Grid.hpp"
	"Simulation/Hotel.hpp"
	"Simulation/Mop.hpp"
	"Simulation/PV.hpp"
	"Simulation/TempSum.hpp"
	"Simulation/HeatPumpController.hpp"
	"Simulation/Components/DataCentre.hpp"
	"Simulation/Components/DataCentreWithASHP.cpp" 
	"Simulation/Components/BasicDataCentre.cpp"
	"Simulation/TaskComponents.hpp"
	"Simulation/TaskData.hpp"
	"Simulation/SiteData.hpp"
	"Simulation/Components/ESS/ESS.cpp"
	"Simulation/Costs/Capex.cpp"
	"Simulation/Costs/Opex.cpp"
	"Simulation/Costs/Compare.hpp"
	"Simulation/Costs/Compare.cpp"
	"Simulation/Costs/CostData.cpp"
	"Simulation/Costs/NetPresentValue.cpp"
	"Simulation/Costs/Usage.cpp"
	"Simulation/Costs/Usage.hpp"
 "Portfolio/Portfolio.cpp")

find_package(Eigen3 CONFIG REQUIRED)
target_link_libraries(Epoch_lib PRIVATE Eigen3::Eigen)
# disallow LGPL code in Eigen
add_compile_definitions("EIGEN_MPL2_ONLY")

find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(Epoch_lib PRIVATE nlohmann_json::nlohmann_json)

find_package(spdlog CONFIG REQUIRED)
target_link_libraries(Epoch_lib PRIVATE spdlog::spdlog)
target_compile_definitions(Epoch_lib PRIVATE SPDLOG_COMPILED_LIB)
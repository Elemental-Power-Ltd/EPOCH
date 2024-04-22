add_library(Epoch_lib STATIC
	"Definitions.hpp"
	"io/FileConfig.hpp"
	"io/FileHandling.cpp"
	"io/FileHandling.hpp"
	"Optimisation/LeagueTable.cpp"
	"Optimisation/LeagueTable.hpp"
	"Optimisation/Optimiser.cpp"
	"Optimisation/Optimiser.hpp"
	"Optimisation/TaskGenerator.cpp"
	"Optimisation/TaskGenerator.hpp"
	"Simulation/Assets.hpp"
	"Simulation/TaskData.hpp"
	"Simulation/Costs.hpp"
	"Simulation/Eload.hpp"
	"Simulation/Grid.hpp"
	"Simulation/Hload.hpp"
	"Simulation/Simulate.cpp"
	"Simulation/Simulate.hpp"
	"io/EpochConfig.cpp"
	"io/EpochConfig.hpp"
	"io/BufferedCSVWriter.cpp"
	"io/BufferedCSVWriter.hpp"
)

find_package(Eigen3 CONFIG REQUIRED)
target_link_libraries(Epoch_lib PRIVATE Eigen3::Eigen)
# disallow LGPL code in Eigen
add_compile_definitions("EIGEN_MPL2_ONLY")

find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(Epoch_lib PRIVATE nlohmann_json::nlohmann_json)

find_package(spdlog CONFIG REQUIRED)
target_link_libraries(Epoch_lib PRIVATE spdlog::spdlog)
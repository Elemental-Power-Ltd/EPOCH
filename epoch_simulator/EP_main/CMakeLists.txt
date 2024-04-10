

if (BUILD_GUI)

	add_executable(EP_APP WIN32
		"EP_main.cpp"
		"EP_main.h"
		"EP_main.rc"
		"Resource.h"
		"GUI/gui.hpp"
		"GUI/gui.cpp"
		"framework.h"
		"targetver.h"
	)

	target_compile_definitions(EP_APP PRIVATE EP_GUI)
	add_definitions(-DUNICODE -D_UNICODE)

else ()
	add_executable(EP_APP EP_main.cpp EP_main.h)

endif()

target_link_libraries(EP_APP PRIVATE Epoch_lib)

find_package(mimalloc CONFIG REQUIRED)
target_link_libraries(EP_APP PRIVATE mimalloc)

find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(EP_APP PRIVATE nlohmann_json::nlohmann_json)

find_package(spdlog CONFIG REQUIRED)
target_link_libraries(EP_APP PRIVATE spdlog::spdlog)



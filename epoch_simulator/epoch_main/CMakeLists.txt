

if (BUILD_GUI)

	add_executable(Epoch WIN32
		"epoch_main.cpp"
		"epoch_main.h"
		"epoch_main.rc"
		"Resource.h"
		"GUI/gui.hpp"
		"GUI/gui.cpp"
		"framework.h"
		"targetver.h"
	)

	target_compile_definitions(Epoch PRIVATE EPOCH_GUI)
	add_definitions(-DUNICODE -D_UNICODE)

else ()
	add_executable(Epoch "epoch_main.cpp" "epoch_main.h")

endif()

target_link_libraries(Epoch PRIVATE Epoch_lib)

find_package(mimalloc CONFIG REQUIRED)
target_link_libraries(Epoch PRIVATE mimalloc)

find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(Epoch PRIVATE nlohmann_json::nlohmann_json)

find_package(spdlog CONFIG REQUIRED)
target_link_libraries(Epoch PRIVATE spdlog::spdlog)



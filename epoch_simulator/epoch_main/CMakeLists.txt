

get_property(isMultiConfig GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if (${isMultiConfig})
	# for simplification, only support Debug and RelWithDebInfo for now
	# these are the build types we have defined in CMakePresets.json
	set(CMAKE_CONFIGURATION_TYPES "Debug;RelWithDebInfo;" CACHE STRING "" FORCE) 
endif()

if (BUILD_GUI)

	add_executable(Epoch WIN32
		"epoch_main.cpp"
		"epoch_main.hpp"
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
	add_executable(Epoch "epoch_main.cpp" "epoch_main.hpp" "ArgHandling.hpp")

endif()

target_link_libraries(Epoch PRIVATE Epoch_lib)

find_package(mimalloc CONFIG REQUIRED)
target_link_libraries(Epoch PRIVATE mimalloc)

find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(Epoch PRIVATE nlohmann_json::nlohmann_json)
set(nlohmann-json_IMPLICIT_CONVERSIONS OFF)

find_package(spdlog CONFIG REQUIRED)
target_link_libraries(Epoch PRIVATE spdlog::spdlog)

find_package(argparse CONFIG REQUIRED)
target_link_libraries(Epoch PRIVATE argparse::argparse)



# Installation Logic
install(TARGETS Epoch
    COMPONENT Epoch
    RUNTIME_DEPENDENCIES
    PRE_EXCLUDE_REGEXES "api-ms-" "ext-ms-"
    POST_EXCLUDE_REGEXES ".*system32/.*\\.dll"
    DIRECTORIES $<TARGET_FILE_DIR:Epoch>)

# using the TARGET_RUNTIME_DLLS generator expression fails to pick up mimalloc-redirect
#  so we use the approach above (see https://stackoverflow.com/a/75065206)


# copy the InputData and Config directories into the install folder
install(DIRECTORY "${CMAKE_SOURCE_DIR}/InputData" DESTINATION "bin")
install(DIRECTORY "${CMAKE_SOURCE_DIR}/Config" DESTINATION "bin")


get_property(isMultiConfig GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if (${isMultiConfig})
	# for simplification, only allow building the python bindings as Release
	set(CMAKE_CONFIGURATION_TYPES "Release;" CACHE STRING "" FORCE) 
endif()

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(epoch_simulator 
"Bindings.cpp"
"Bindings.hpp"
"Simulate_py.cpp"
"Simulate_py.hpp")

target_link_libraries(epoch_simulator PRIVATE Epoch_lib)

# Installation Logic
install(TARGETS epoch_simulator DESTINATION "bin")
install(FILES $<TARGET_RUNTIME_DLLS:epoch_simulator> TYPE BIN)

# copy the InputData and Config directories into the install folder
install(DIRECTORY "${CMAKE_SOURCE_DIR}/InputData" DESTINATION "bin")

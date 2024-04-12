
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(epoch_simulator 
"Bindings.cpp"
"Bindings.hpp"
"Simulate_py.cpp"
"Simulate_py.hpp")

target_link_libraries(epoch_simulator PRIVATE Epoch_lib)

# Installation Logic
install(FILES $<TARGET_RUNTIME_DLLS:epoch_simulator> TYPE BIN)

# copy the InputData directory into the install folder
install(DIRECTORY "${CMAKE_SOURCE_DIR}/InputData" DESTINATION "bin")
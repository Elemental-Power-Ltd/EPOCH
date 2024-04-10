
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(EPSimulator 
"Bindings.cpp"
"Bindings.hpp"
"Simulate_py.cpp"
"Simulate_py.hpp")

target_link_libraries(EPSimulator PRIVATE Epoch_lib)



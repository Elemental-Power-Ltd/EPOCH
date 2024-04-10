
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(epoch_simulator 
"Bindings.cpp"
"Bindings.hpp"
"Simulate_py.cpp"
"Simulate_py.hpp")

target_link_libraries(epoch_simulator PRIVATE Epoch_lib)



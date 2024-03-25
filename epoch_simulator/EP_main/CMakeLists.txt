add_executable(EP_APP EP_main.cpp EP_main.h)

target_link_libraries(EP_APP PRIVATE EP)

find_package(mimalloc CONFIG REQUIRED)
target_link_libraries(EP_APP PRIVATE mimalloc)

find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(EP_APP PRIVATE nlohmann_json::nlohmann_json)

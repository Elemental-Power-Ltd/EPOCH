
add_executable(epoch_test test_main.cpp test_task_data.cpp test_pv.cpp test_total.cpp test_costs.cpp)

target_link_libraries(epoch_test PRIVATE Epoch_lib)

find_package(spdlog CONFIG REQUIRED)
target_link_libraries(epoch_test PRIVATE spdlog::spdlog)

find_package(GTest CONFIG REQUIRED)
target_link_libraries(epoch_test PRIVATE GTest::gtest_main)

find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(epoch_test PRIVATE nlohmann_json)

include (GoogleTest)
gtest_discover_tests(epoch_test WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/epoch_test")
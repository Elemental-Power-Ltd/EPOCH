
add_executable(EP_TEST test.cpp)

target_link_libraries(EP_TEST PRIVATE EP)

find_package(GTest CONFIG REQUIRED)
target_link_libraries(EP_TEST PRIVATE GTest::gtest_main)

find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(EP_TEST PRIVATE nlohmann_json)

include (GoogleTest)
gtest_discover_tests(EP_TEST WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/EP_Test")
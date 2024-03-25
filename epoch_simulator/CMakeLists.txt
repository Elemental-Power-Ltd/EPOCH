cmake_minimum_required (VERSION 3.28)

project(Delta LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)

add_subdirectory("EP")
add_subdirectory("EP_main")

set_property(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT EP_APP)

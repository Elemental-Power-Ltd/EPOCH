cmake_minimum_required (VERSION 3.28)

project(Delta LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)

add_subdirectory("EP")

if(PYBIND)
	add_subdirectory("EP_py")
else()
	add_subdirectory("EP_main")
endif()

# Configure Testing
if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)
	include(CTest)

	enable_testing()

	if(BUILD_TESTING)
		add_subdirectory(EP_Test)
	endif()

endif()

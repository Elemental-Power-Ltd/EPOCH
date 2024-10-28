cmake_minimum_required (VERSION 3.22)

project(Epoch LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)

# Set strict compiler error/warning settings
# When using add_compile_options, this must be done before creating any targets
if(MSVC)
  add_compile_options(/W4 /WX /wd4100)

else()
  add_compile_options(-Wall -Wextra -Wpedantic -Werror )
  # FIXME
  # These constraints need tightening
  add_compile_options(-Wno-error=unused-parameter -Wno-error=reorder)

endif()

add_subdirectory("epoch_lib")

if(PYBIND)
	add_subdirectory("epoch_py")
else()
	add_subdirectory("epoch_main")
endif()

# Configure Testing
if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)
	include(CTest)

	enable_testing()

	if(BUILD_TESTING)
		add_subdirectory(epoch_test)
	endif()

endif()

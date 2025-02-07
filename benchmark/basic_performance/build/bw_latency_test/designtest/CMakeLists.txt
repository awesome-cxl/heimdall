cmake_minimum_required(VERSION 3.22)

# C++ requirement
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(cxl_perf_app_dt)
option(BUILD_AS_LIBRARY "Build project as a library" ON)
if(NOT DEFINED MACHINE_TYPE)
  message(STATUS "MACHINE_TYPE is not set, defaulting to mockup")
  set(MACHINE_TYPE 3) # mockup
endif()
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../../design_test
                 cxl_perf_app_designtest)

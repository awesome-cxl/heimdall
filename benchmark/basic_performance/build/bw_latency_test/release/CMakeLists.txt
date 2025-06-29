cmake_minimum_required(VERSION 3.22)

# C++ requirement
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(cxl_perf_app_release)
option(BUILD_AS_LIBRARY "Build project as a library" OFF)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../ cxl_perf_app_release)

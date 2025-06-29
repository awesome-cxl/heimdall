cmake_minimum_required(VERSION 3.22)

# C++ requirement
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set the build type to Release if not specified
set(CMAKE_BUILD_TYPE Release)
set(CMAKE_CXX_FLAGS_RELEASE "-O0")

project(cxl_perf_app_cache)

add_subdirectory(../../../../../extern/yaml-cpp ${CMAKE_CURRENT_BINARY_DIR}/yaml-cpp)

file(GLOB src_files ../../../src/main_cache.cpp
     ../../../src/utils/input_parser.cpp ../../../src/utils/logger.cpp
     ../../../src/utils/timer.cpp)

add_executable(cxl_perf_app_cache ${src_files})

set_target_properties(
  cxl_perf_app_cache
  PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/bin/
             LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/lib/
             ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/lib/
             COMPILE_WARNING_AS_ERROR OFF)

target_link_libraries(cxl_perf_app_cache PUBLIC yaml-cpp)

target_include_directories(
  cxl_perf_app_cache
  PUBLIC ../../../src/machine/x86/pointer_chasing ../../../src
         ../../../src/core ../../../src/utils ../../../../../extern/yaml-cpp)

cmake_minimum_required(VERSION 3.22)

# C++ requirement
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set the build type to Release if not specified
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
  set(CMAKE_BUILD_TYPE Debug)
  message(STATUS "Build type: Debug")
elseif(CMAKE_BUILD_TYPE STREQUAL "Release")
  set(CMAKE_BUILD_TYPE Release)
  message(STATUS "Build type: Release")
else()
  set(CMAKE_BUILD_TYPE Release)
  message(STATUS "Build type: Release")
endif()

if(MACHINE_TYPE EQUAL 1) # x86
  set(CMAKE_CXX_FLAGS_RELEASE "-O0")
  set(CMAKE_CXX_FLAGS_RELEASE "-mavx512f")
elseif(MACHINE_TYPE EQUAL 2) # arm
  set(CMAKE_CXX_FLAGS_RELEASE "-O0")
  set(CMAKE_CXX_FLAGS_RELEASE "-march=armv8-a+sve")
elseif(MACHINE_TYPE EQUAL 3) # mockup
  message(STATUS "Mockup Settings")
endif()

project(cxl_perf_app)

add_subdirectory(../../../../extern/yaml-cpp ${CMAKE_CURRENT_BINARY_DIR}/yaml-cpp)

add_definitions(-DCORE_NUM_PER_SOCKET_DEF=${CORE_NUM_PER_SOCKET})
add_definitions(-DMACHINE_TYPE_DEF=${MACHINE_TYPE})
add_definitions(-DMAX_SOCKET_NUM_DEF=${MAX_SOCKET_NUM})

file(
  GLOB
  src_files
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/main_bw.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/memory/*.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/utils/*.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/core/*.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/tasks/*.cpp)

if(MACHINE_TYPE EQUAL 1) # x86
  file(GLOB x86_sources
       ${CMAKE_CURRENT_SOURCE_DIR}/../../src/machine/x86/ld_st/*.cpp)
  if(x86_sources)
    list(APPEND src_files ${x86_sources})
    message(STATUS "x86 sources: ${src_files}")
  endif()
elseif(MACHINE_TYPE EQUAL 2) # arm
  file(GLOB arm_sources ${CMAKE_CURRENT_SOURCE_DIR}/../../src/machine/arm/*.cpp)
  if(arm_sources)
    list(APPEND src_files ${arm_sources})
    message(STATUS "ARM sources: ${src_files}")
  endif()
elseif(MACHINE_TYPE EQUAL 3) # mockup
  file(GLOB mockup_sources
       ${CMAKE_CURRENT_SOURCE_DIR}/../../src/machine/mockup/*.cpp)
  if(mockup_sources)
    list(APPEND src_files ${mockup_sources})
    message(STATUS "Mockup sources: ${src_files}")
  endif()
endif()

if(BUILD_AS_LIBRARY STREQUAL "ON")
  add_library(cxl_perf_app STATIC ${src_files})
else()
  add_executable(cxl_perf_app ${src_files})
endif()

set_target_properties(
  cxl_perf_app
  PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/bin/
             LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/lib/
             ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/lib/
             COMPILE_WARNING_AS_ERROR OFF)

find_library(NUMA_LIBRARY numa REQUIRED)
if(NOT NUMA_LIBRARY)
  message(FATAL_ERROR "NUMA library not found. Please install libnuma-dev.")
else()
  message(STATUS "NUMA library found: ${NUMA_LIBRARY}")
endif()

target_link_libraries(cxl_perf_app PUBLIC yaml-cpp)
target_link_libraries(cxl_perf_app PRIVATE ${NUMA_LIBRARY})

target_include_directories(
  cxl_perf_app
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../../src
         ${CMAKE_CURRENT_SOURCE_DIR}/../../src/machine
         ${CMAKE_CURRENT_SOURCE_DIR}/../../src/memory
         ${CMAKE_CURRENT_SOURCE_DIR}/../../src/utils
         ${CMAKE_CURRENT_SOURCE_DIR}/../../src/core
         ${CMAKE_CURRENT_SOURCE_DIR}/../../src/tasks
         ${CMAKE_CURRENT_SOURCE_DIR}/../../extern/yaml-cpp)

if(MACHINE_TYPE EQUAL 1) # x86
  target_include_directories(
    cxl_perf_app PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../../src/machine/x86/ld_st)
elseif(MACHINE_TYPE EQUAL 2) # arm
  target_include_directories(
    cxl_perf_app PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../../src/machine/arm)
elseif(MACHINE_TYPE EQUAL 3) # mockup
  target_include_directories(
    cxl_perf_app PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../../src/machine/mockup)
endif()

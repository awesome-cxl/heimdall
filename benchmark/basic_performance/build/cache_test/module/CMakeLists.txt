cmake_minimum_required(VERSION 3.10)
project(cxl_perf_kernel_module)

execute_process(
  COMMAND uname -r
  OUTPUT_VARIABLE KERNEL_VERSION
  OUTPUT_STRIP_TRAILING_WHITESPACE)

set(KERNEL_DIR /lib/modules/${KERNEL_VERSION}/build)

set(KERNEL_SRC_DIR ${CMAKE_SOURCE_DIR}/../../../src/machine/x86/pointer_chasing)
set(OUTPUT_DIR ${CMAKE_BINARY_DIR}/kernel_module)

if(NOT EXISTS ${KERNEL_SRC_DIR})
  message(
    FATAL_ERROR
      "Kernel module source directory does not exist: ${KERNEL_SRC_DIR}")
endif()

add_custom_target(
  build_kernel_module
  COMMAND make -C ${KERNEL_DIR} M=${KERNEL_SRC_DIR} modules
  WORKING_DIRECTORY ${KERNEL_SRC_DIR}
  COMMENT "Building kernel module...")

add_custom_target(
  clean_kernel_module
  COMMAND make -C ${KERNEL_DIR} M=${KERNEL_SRC_DIR} clean
  WORKING_DIRECTORY ${KERNEL_SRC_DIR}
  COMMENT "Cleaning kernel module...")


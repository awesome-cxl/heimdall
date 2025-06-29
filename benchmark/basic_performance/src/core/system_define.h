/*
 *
 * MIT License
 *
 * Copyright (c) 2025 Jangseon Park
 * Affiliation: University of California San Diego CSE
 * Email: jap036@ucsd.edu
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */

#ifndef CXL_PERF_APP_DT_SYSTEM_DEFINE_H
#define CXL_PERF_APP_DT_SYSTEM_DEFINE_H
#include <cstdint>
#include <machine_define.h>

enum class NumaId : uint32_t {
  NODE_0 = 0,
  NODE_1 = 1,
  NODE_2 = 2,
  NODE_3 = 3,
  NODE_4 = 4,
  NODE_5 = 5,
  MAX_NUMA_ID = 6,
};

enum SocketId : uint32_t {
  SOCKET_0 = 0,
  SOCKET_1 = 1,
  MAX_SOCKET_ID = 2,
};

enum class JobId : uint32_t {
  BANDWIDTH_LATENCY = 100,
  BANDWIDTH = 101,
  LATENCY = 102,
  POINTER_CHASE = 200,
};

enum class LoadStoreType : uint32_t {
  LOAD = 0,
  STORE = 1,
  NT_LOAD = 2,
  NT_STORE = 3,
  LOAD_WITH_FLUSH = 4,
  STORE_WITH_FLUSH = 5,
};

enum class MachineType : uint32_t {
  x86 = 1,
  ARM = 2,
  MOCKUP = 3,
  CURRENT_MACHINE = MACHINE_TYPE_DEF,
};

enum class MemAllocType : uint32_t {
  CONTIGUOUS_HUGE_PAGE = 0,
  NON_CONTIGUOUS_HUGE_PAGE = 1,
};

enum class CHASING_TYPE : uint32_t {
  CHASING_TYPE_LINEAR = 0,
  CHASING_TYPE_RANDOM,
  CHASING_TYPE_MAX
};

enum class LatencyPattern : uint32_t {
  STRIDE_LAT = 0,
  RANDOM_PC_LAT = 1,
  LATENCY_PATTERN_MAX
};

enum class BwPattern : uint32_t {
  STRIDE_BW = 0,
  SIMPLE_INCREMENT_BW = 1,
  BW_PATTERN_MAX
};

enum class BwPatternSize : uint32_t {
  SIZE_64B = 64,
  SIZE_128B = 128,
  SIZE_256B = 256,
  SIZE_512B = 512,
};

class BlockSize {
public:
  static const uint64_t BLOCK_64B = 64;
  static const uint64_t BLOCK_128B = 128;
  static const uint64_t BLOCK_256B = 256;
  static const uint64_t BLOCK_512B = 512;
};

class MEMUNIT {
public:
  static const uint64_t KiB = 1024;
  static const uint64_t MiB = 1024 * 1024;
  static const uint64_t GiB = 1024 * 1024 * 1024;
};

class CoreConfig {
public:
  static const uint64_t CORE_NUMBER_PER_SOCKET = CORE_NUM_PER_SOCKET_DEF;
  static const uint64_t MAX_SOCKET_NUM = MAX_SOCKET_NUM_DEF;
};

#endif // CXL_PERF_APP_DT_SYSTEM_DEFINE_H

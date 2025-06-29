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

#ifndef CXL_PERF_APP_DATA_STRUCTURE_H
#define CXL_PERF_APP_DATA_STRUCTURE_H

#include <chrono>
#include <condition_variable>
#include <core/system_define.h>
#include <functional>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>

struct WorkerTestLog {
  uint64_t size;
  uint64_t latency;
};

struct JobInfo {
  JobId job_id;
  uint32_t num_threads;
  uint64_t lt_pattern_block_size;
  uint64_t lt_pattern_access_size;
  uint64_t lt_pattern_stride_size;
  uint64_t delay;
  NumaId numa_id;
  SocketId socket_id;
  LoadStoreType ldst_type;
  MemAllocType mem_alloc_type;
  LatencyPattern latency_pattern;
  BwPattern bw_pattern;
  BwPatternSize bw_load_pattern_block_size;
  BwPatternSize bw_store_pattern_block_size;
  uint32_t pattern_iteration;
  uint64_t thread_buffer_size;
};

struct WorkerContext {
  uint32_t core_id;
  JobId job_id;
  uint8_t *addr;
  uint8_t *end_addr;
  uint64_t size;
  uint64_t lt_pattern_access_size;
  uint64_t lt_pattern_block_size;
  uint64_t lt_pattern_stride_size;
  uint64_t delay;
  uint64_t access_cnt;
  LoadStoreType ldst_type;
  LatencyPattern latency_pattern;
  BwPattern bw_pattern;
  BwPatternSize bw_load_pattern_block_size;
  BwPatternSize bw_store_pattern_block_size;
  NumaId numa_id;
  SocketId socket_id;
  std::function<void(std::shared_ptr<WorkerContext>)> func;
  std::condition_variable complete;
  std::condition_variable ready;
  std::condition_variable subop_stop;
  std::atomic<bool> stop_flag;
  std::mutex mutex;
  WorkerTestLog log;
  MemAllocType mem_alloc_type;
  uint32_t pattern_iteration;

  void get_work_descriptor(const std::shared_ptr<JobInfo> &job_info,
                           uint32_t coreid) {
    core_id = coreid;
    job_id = job_info->job_id;
    this->addr = nullptr; // addr;
    this->size = job_info->thread_buffer_size;
    this->end_addr = nullptr; // addr + size;
    lt_pattern_access_size = job_info->lt_pattern_access_size;
    lt_pattern_block_size = job_info->lt_pattern_block_size;
    lt_pattern_stride_size = job_info->lt_pattern_stride_size;
    delay = job_info->delay;
    access_cnt = size / lt_pattern_access_size;
    ldst_type = job_info->ldst_type;
    latency_pattern = job_info->latency_pattern;
    bw_pattern = job_info->bw_pattern;
    numa_id = job_info->numa_id;
    socket_id = job_info->socket_id;
    mem_alloc_type = job_info->mem_alloc_type;
    pattern_iteration = job_info->pattern_iteration;
    bw_load_pattern_block_size = job_info->bw_load_pattern_block_size;
    bw_store_pattern_block_size = job_info->bw_store_pattern_block_size;
  }
};

struct WorkerInfo {
  void *virtual_addr;
  uint64_t init_size;
  uint32_t num_threads;
  NumaId numa_id;
  SocketId socket_id;
  MemAllocType mem_alloc_type;
  std::vector<std::thread> workers;
  std::vector<std::shared_ptr<WorkerContext>> worker_ctx;
};

using WorkFunc = std::function<void(std::shared_ptr<WorkerContext>)>;

using StrideFunc = std::function<void(
    uint8_t *start_addr, uint64_t size, uint64_t skip, uint64_t delay,
    uint64_t count, uint64_t block_size, uint64_t *time_log)>;

typedef struct pchasing_args {
  uint64_t in_block_num;
  uint64_t in_stride_size;
  uint64_t in_repeat;
  uint64_t in_core_id;
  uint64_t in_node_id;
  uint64_t in_use_flush;
  uint64_t in_access_order;
  uint64_t in_dimm_start_addr_phys;
  uint64_t in_dimm_test_size;
  uint64_t in_test_size;
  uint64_t out_latency_cycle_ld;
  uint64_t out_latency_cycle_st;
  uint64_t out_total_cycle_ld;
  uint64_t out_total_cycle_st;
  uint64_t out_total_ns_ld;
  uint64_t out_total_ns_st;
} pchasing_args_t;

#endif // CXL_PERF_APP_DATA_STRUCTURE_H

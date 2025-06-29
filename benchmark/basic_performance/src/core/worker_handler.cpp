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

#include <cerrno>
#include <core/system_define.h>
#include <core/worker_handler.h>
#include <cstring>
#include <iostream>
#include <memory/mem_allocator.h>
#include <pthread.h>
#include <sched.h>

WorkerHandler::WorkerHandler() : _worker_info(std::make_shared<WorkerInfo>()) {}

WorkerHandler::~WorkerHandler() {}

void WorkerHandler::initialize(const std::shared_ptr<JobInfo> &job_info,
                               Logger &logger) {
  _worker_info->init_size =
      job_info->thread_buffer_size * job_info->num_threads;
  _worker_info->num_threads = job_info->num_threads;
  _worker_info->numa_id = job_info->numa_id;
  _worker_info->socket_id = job_info->socket_id;
  _worker_info->mem_alloc_type = job_info->mem_alloc_type;

  for (int i = 0; i < job_info->num_threads; i++) {
    auto ctx = std::make_shared<WorkerContext>();
    ctx->get_work_descriptor(job_info, i);
    ctx->func = nullptr;
    ctx->log = {0, 0};
    ctx->stop_flag = false;
    _worker_info->worker_ctx.emplace_back(ctx);
  }

  logger.append(generate_test_info(job_info));
  for (int i = 0; i < job_info->num_threads; i++) {
    _worker_info->workers.emplace_back(WorkerHandler::work,
                                       _worker_info->worker_ctx[i]);
    set_thread_affinity(_worker_info->workers[i],
                        get_core_number(i, job_info->socket_id), i);
  }
}

std::size_t WorkerHandler::get_core_number(int thread_num, SocketId socket_id) {
  int base_offset =
      static_cast<uint64_t>(socket_id) * CoreConfig::CORE_NUMBER_PER_SOCKET;
  if (thread_num >= CoreConfig::CORE_NUMBER_PER_SOCKET) {
    base_offset +=
        (CoreConfig::MAX_SOCKET_NUM - 1) * CoreConfig::CORE_NUMBER_PER_SOCKET +
        1;
  }
  return base_offset + thread_num;
}

std::string
WorkerHandler::generate_test_info(const std::shared_ptr<JobInfo> &job_info) {
  std::string access_type = static_cast<int>(job_info->socket_id) ==
                                    static_cast<int>(job_info->numa_id)
                                ? "LOCAL"
                                : "REMOTE";
  access_type += "_" + std::to_string(static_cast<int>(job_info->socket_id)) +
                 "_" + std::to_string(static_cast<int>(job_info->numa_id));
  std::string ldst_type =
      job_info->ldst_type == LoadStoreType::LOAD ? "LOAD" : "STORE";
  std::string mem_alloc_type =
      job_info->mem_alloc_type == MemAllocType::CONTIGUOUS_HUGE_PAGE
          ? "CONTIGUOUS_HUGE_PAGE"
          : "NON_CONTIGUOUS_HUGE_PAGE";
  std::string latency_pattern =
      job_info->latency_pattern == LatencyPattern::STRIDE_LAT ? "STRIDE_LAT"
                                                              : "RANDOM_PC_LAT";
  std::string bw_pattern =
      job_info->bw_pattern == BwPattern::STRIDE_BW ? "STRIDE_BW" : "SIMPLE_BW";
  std::string bw_load_pattern_block_size =
      job_info->bw_load_pattern_block_size == BwPatternSize::SIZE_64B
          ? "SIZE_64B"
      : job_info->bw_load_pattern_block_size == BwPatternSize::SIZE_128B
          ? "SIZE_128B"
      : job_info->bw_load_pattern_block_size == BwPatternSize::SIZE_256B
          ? "SIZE_256B"
          : "SIZE_512B";

  std::string bw_store_pattern_block_size =
      job_info->bw_store_pattern_block_size == BwPatternSize::SIZE_64B
          ? "SIZE_64B"
      : job_info->bw_store_pattern_block_size == BwPatternSize::SIZE_128B
          ? "SIZE_128B"
      : job_info->bw_store_pattern_block_size == BwPatternSize::SIZE_256B
          ? "SIZE_256B"
          : "SIZE_512B";

  std::string msg =
      "========================================================================"
      "===================\n"
      "Test Information:\n"
      "Buffer Size: " +
      std::to_string(job_info->thread_buffer_size / MEMUNIT::MiB) + "MiB\n" +
      "Number of Threads: " + std::to_string(_worker_info->num_threads) + "\n" +
      "Job Id: " + std::to_string(static_cast<int>(job_info->job_id)) + "\n" +
      "Access Type: " + access_type + "\n" + "LoadStore Type: " + ldst_type +
      "\n"
      "Block Size: " +
      std::to_string(job_info->lt_pattern_block_size) +
      " bytes\n"
      "Mem alloc Type: " +
      mem_alloc_type +
      "\n"
      "Latency Pattern: " +
      latency_pattern +
      "\n"
      "Bandwidth Pattern: " +
      bw_pattern +
      "\n"
      "Bandwidth Load Pattern Block Size: " +
      bw_load_pattern_block_size +
      "\n"
      "Bandwidth Store Pattern Block Size: " +
      bw_store_pattern_block_size +
      "\n"
      "========================================================================"
      "===================\n";
  return msg;
}

void WorkerHandler::start() {
  std::cout << "Start worker threads" << std::endl;
  auto worker_info = get_worker_info();
  for (int i = 0; i < worker_info->num_threads; ++i) {
    {
      std::lock_guard<std::mutex> lock(worker_info->worker_ctx[i]->mutex);
      auto worker = worker_info->worker_ctx[i];
      worker_info->worker_ctx[i]->func =
          [this, i, worker](const std::shared_ptr<WorkerContext> &ctx) {
            assign_handler(i, worker);
          };
    }
    worker_info->worker_ctx[i]->ready.notify_all();
  }
}

void WorkerHandler::wait() {
  std::cout << "Stopping worker threads" << std::endl;
}

void WorkerHandler::wrap_up() {
  std::cout << "Wrapping up worker threads" << std::endl;
  for (auto &worker : _worker_info->workers) {
    if (worker.joinable()) {
      worker.join();
    }
  }
}

void WorkerHandler::work(std::shared_ptr<WorkerContext> ctx) {
  try {
    {
      std::unique_lock<std::mutex> lock(ctx->mutex);
      ctx->ready.wait(lock, [&] { return ctx->func != nullptr; });
    }
    ctx->addr = static_cast<uint8_t *>(MemAllocator::allocate(
        ctx->size, static_cast<int>(ctx->numa_id), ctx->mem_alloc_type));
    ctx->end_addr = ctx->addr + ctx->size;
    std::memset(ctx->addr, 1, ctx->size);

    ctx->func(ctx);

    MemAllocator::deallocate(ctx->addr, ctx->size, ctx->mem_alloc_type);
  } catch (const std::exception &e) {
    std::cerr << "Error in Worker " << ctx->core_id << ": " << e.what()
              << std::endl;

    if (ctx->addr) {
      MemAllocator::deallocate(ctx->addr, ctx->size, ctx->mem_alloc_type);
    }
  }
}

std::shared_ptr<WorkerInfo> WorkerHandler::get_worker_info() const {
  return _worker_info;
}

void WorkerHandler::set_thread_affinity(std::thread &worker,
                                        std::size_t core_id,
                                        uint32_t thread_id) {
  pthread_t thread = worker.native_handle();
  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  CPU_SET(core_id, &cpuset);
  int rc = pthread_setaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
  if (rc != 0) {
    std::cerr << "Error calling pthread_setaffinity_np: " << rc << std::endl;
  } else {
    std::cout << "Worker " << thread_id << " is set to core " << core_id
              << std::endl;
  }
  std::cout << "Thread " << thread_id << " is bound to CPU cores: ";
  for (int i = 0; i < CPU_SETSIZE; ++i) {
    if (CPU_ISSET(i, &cpuset)) {
      std::cout << i << " ";
    }
  }
  std::cout << std::endl;

  sched_param schedParam;
  schedParam.sched_priority = sched_get_priority_max(SCHED_FIFO);
  rc = pthread_setschedparam(thread, SCHED_FIFO, &schedParam);
  if (rc != 0) {
    std::cerr << "Error calling pthread_setschedparam: "
              << std::to_string(errno) << std::endl;
  } else {
    std::cout << "Thread " << core_id << " priority set to maximum."
              << std::endl;
  }
}

WorkerHandlerForBandwidth::WorkerHandlerForBandwidth()
    : WorkerHandler(),
      _stride_bw_handler(std::make_shared<StrideBandwidthPatternHandler>()),
      _simple_bw_handler(
          std::make_shared<SimpleLdStBandwidthPatternHandler>()) {
  _bw_pattern_handler_map[BwPattern::STRIDE_BW] = _stride_bw_handler;
  _bw_pattern_handler_map[BwPattern::SIMPLE_INCREMENT_BW] = _simple_bw_handler;
}

void WorkerHandlerForBandwidth::assign_handler(
    int thread_num, std::shared_ptr<WorkerContext> ctx) {
  auto it = _bw_pattern_handler_map.find(ctx->bw_pattern);
  if (it == _bw_pattern_handler_map.end()) {
    throw std::runtime_error("Invalid bandwidth pattern");
  }
  it->second->handle(ctx);
}

void WorkerHandlerForBandwidth::report(Logger &logger) {
  uint64_t bandwidth_sum = 0;
  for (auto &worker_ctx : get_worker_info()->worker_ctx) {
    bandwidth_sum +=
        worker_ctx->log.size * 1e9 / worker_ctx->log.latency / MEMUNIT::MiB;
    std::string msg =
        "Worker : [" + std::to_string(worker_ctx->core_id) + "] " +
        "Latency : " + std::to_string(worker_ctx->log.latency) + " ns, " +
        "Size : " + std::to_string(worker_ctx->log.size) + " bytes, " +
        "Bandwidth : " +
        std::to_string(worker_ctx->log.size * 1e9 / worker_ctx->log.latency /
                       MEMUNIT::MiB) +
        " MiB/s";
    logger.append(msg);
  }
  logger.append("Total Bandwidth : " + std::to_string(bandwidth_sum) +
                " MiB/s");
}

void WorkerHandlerForBandwidth::wait() {
  auto worker_info = get_worker_info();
  std::this_thread::sleep_for(std::chrono::seconds(10));
  std::cout << "Send signal to stop worker threads" << std::endl;
  for (int i = 0; i < worker_info->num_threads; ++i) {
    {
      std::lock_guard<std::mutex> lock(worker_info->worker_ctx[i]->mutex);
      worker_info->worker_ctx[i]->stop_flag = true;
    }
    worker_info->worker_ctx[i]->subop_stop.notify_all();
  }
}

WorkerHandlerForLatency::WorkerHandlerForLatency()
    : WorkerHandler(),
      _stride_latency_handler(std::make_shared<StrideLatencyPatternHandler>()),
      _pointer_chase_latency_handler(
          std::make_shared<PointerChaseLatencyPatternHandler>()) {}

void WorkerHandlerForLatency::assign_handler(
    int thread_num, std::shared_ptr<WorkerContext> ctx) {
  auto it = _latency_pattern_handler_map.find(ctx->latency_pattern);
  if (it == _latency_pattern_handler_map.end()) {
    throw std::runtime_error("Invalid delay pattern");
  }
  it->second->handle(ctx);
}

void WorkerHandlerForLatency::report(Logger &logger) {
  uint64_t latency_sum = 0;
  for (auto &worker_ctx : get_worker_info()->worker_ctx) {
    latency_sum += worker_ctx->log.latency;
    std::string msg =
        "Worker : [" + std::to_string(worker_ctx->core_id) + "] " +
        "Latency : " + std::to_string(worker_ctx->log.latency) + " ns";
    logger.append(msg);
  }
  logger.append("Average Latency : " +
                std::to_string(latency_sum / get_worker_info()->num_threads) +
                " ns");
}

WorkerHandlerForBwVsLatency::WorkerHandlerForBwVsLatency()
    : WorkerHandler(),
      _stride_latency_handler(std::make_shared<StrideLatencyPatternHandler>()),
      _simple_bw_handler(std::make_shared<SimpleLdStBandwidthPatternHandler>()),
      _pointer_chase_latency_handler(
          std::make_shared<PointerChaseLatencyPatternHandler>()),
      _stride_bw_handler(std::make_shared<StrideBandwidthPatternHandler>()) {
  _latency_pattern_handler_map[LatencyPattern::STRIDE_LAT] =
      _stride_latency_handler;
  _latency_pattern_handler_map[LatencyPattern::RANDOM_PC_LAT] =
      _pointer_chase_latency_handler;
  _bw_pattern_handler_map[BwPattern::STRIDE_BW] = _stride_bw_handler;
  _bw_pattern_handler_map[BwPattern::SIMPLE_INCREMENT_BW] = _simple_bw_handler;
}

void WorkerHandlerForBwVsLatency::assign_handler(
    int thread_num, std::shared_ptr<WorkerContext> ctx) {
  if (thread_num == 0) {
    auto it = _latency_pattern_handler_map.find(ctx->latency_pattern);
    if (it == _latency_pattern_handler_map.end()) {
      throw std::runtime_error("Invalid delay pattern");
    }
    it->second->handle(ctx);
  } else {
    auto it = _bw_pattern_handler_map.find(ctx->bw_pattern);
    if (it == _bw_pattern_handler_map.end()) {
      throw std::runtime_error("Invalid bandwidth pattern");
    }
    it->second->handle(ctx);
  }
}

void WorkerHandlerForBwVsLatency::wait() {
  auto worker_info = get_worker_info();
  std::cout << "Stopping worker threads" << std::endl;
  {
    std::unique_lock<std::mutex> lock(worker_info->worker_ctx[0]->mutex);
    worker_info->worker_ctx[0]->complete.wait(lock);
  }

  std::cout << "Send signal to stop worker threads" << std::endl;
  for (int i = 1; i < worker_info->num_threads; ++i) {
    {
      std::lock_guard<std::mutex> lock(worker_info->worker_ctx[i]->mutex);
      worker_info->worker_ctx[i]->stop_flag = true;
    }
    worker_info->worker_ctx[i]->subop_stop.notify_all();
  }
}

void WorkerHandlerForBwVsLatency::report(Logger &logger) {
  uint64_t bandwidth_sum = 0;
  for (int i = 1; i < get_worker_info()->num_threads; i++) {
    auto ctx = get_worker_info()->worker_ctx[i];
    bandwidth_sum += ctx->log.size * 1e9 / ctx->log.latency / MEMUNIT::MiB;
    std::string msg =
        "Worker : [" + std::to_string(ctx->core_id) + "] " +
        "Latency : " + std::to_string(ctx->log.latency) + " ns, " +
        "Size : " + std::to_string(ctx->log.size) + " bytes, " +
        "Bandwidth : " +
        std::to_string(ctx->log.size * 1e9 / ctx->log.latency / MEMUNIT::MiB) +
        " MiB/s";
    logger.append(msg);
  }
  logger.append("Total Bandwidth : " + std::to_string(bandwidth_sum) +
                " MiB/s");
  logger.append("Measured Latency : " +
                std::to_string(get_worker_info()->worker_ctx[0]->log.latency) +
                " ns");
}

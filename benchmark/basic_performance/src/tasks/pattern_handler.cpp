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

#include <tasks/pattern_handler.h>

void PatternHandler::prepare(const std::shared_ptr<WorkerContext> &ctx) {
  _mem_utils.flush_cache(ctx->addr, ctx->size);
};

bool PatternHandler::check_stop_condition(
    const std::shared_ptr<WorkerContext> &ctx) {
  bool return_flag = false;
  {
    std::unique_lock<std::mutex> lock(ctx->mutex);
    if (ctx->subop_stop.wait_for(lock, std::chrono::milliseconds(1),
                                 [ctx]() { return ctx->stop_flag.load(); })) {
      return_flag = true;
    }
  }
  return return_flag;
}

void PatternHandler::wrapup() {

};

void StrideBandwidthPatternHandler::handle(std::shared_ptr<WorkerContext> ctx) {
  uint64_t access_size = ctx->lt_pattern_access_size;
  uint64_t stride_size = ctx->lt_pattern_stride_size;
  uint64_t access_count = ctx->access_cnt;
  uint64_t block_size = ctx->lt_pattern_block_size;
  uint64_t latency = ctx->delay;
  uint8_t *addr = ctx->addr;
  uint8_t *end_addr = ctx->end_addr;
  uint64_t latency_buf = 0;
  WorkerTestLog &log = ctx->log;
  uint64_t thread_buffer_size = ctx->size;
  if (stride_size * access_count > thread_buffer_size) {
    access_count = thread_buffer_size / stride_size;
  }
  prepare(ctx);
  auto func = _stride_pattern.get(ctx->ldst_type);
  if (func == nullptr) {
    std::cerr << "Error: Invalid StrideFunc for LoadStoreType: "
              << static_cast<int>(ctx->ldst_type) << std::endl;
    return;
  }
  while (true) {
    func(addr, access_size, stride_size, latency, access_count, block_size,
         &latency_buf);
    log.latency += latency_buf;
    log.size += access_size * access_count;
    addr += stride_size * access_count;
    if (addr + access_size * access_count >= end_addr) {
      addr = ctx->addr;
    }
    if (check_stop_condition(ctx)) {
      break;
    }
  };
}

void StrideLatencyPatternHandler::handle(std::shared_ptr<WorkerContext> ctx) {
  uint64_t access_size = ctx->lt_pattern_access_size;
  uint64_t stride_size = ctx->lt_pattern_stride_size;
  uint64_t access_count = ctx->access_cnt;
  uint64_t block_size = ctx->lt_pattern_block_size;
  uint64_t delay = ctx->delay;
  uint8_t *addr = ctx->addr;
  uint8_t *end_addr = ctx->end_addr;
  uint64_t latency_buf = 0, latency = 0;
  WorkerTestLog &log = ctx->log;
  LoadStoreType ldst_type = ctx->ldst_type;
  uint32_t pattern_iter = ctx->pattern_iteration;
  uint64_t thread_buffer_size = ctx->size;

  int iteration = 0;
  if (stride_size * access_count > thread_buffer_size) {
    access_count = thread_buffer_size / stride_size;
  }
  if (ldst_type == LoadStoreType::LOAD) {
    ldst_type = LoadStoreType::LOAD_WITH_FLUSH;
  } else if (ldst_type == LoadStoreType::STORE) {
    ldst_type = LoadStoreType::STORE_WITH_FLUSH;
  }

  prepare(ctx);
  auto func = _stride_pattern.get(ldst_type);
  if (func == nullptr) {
    std::cerr << "Error: Invalid StrideFunc for LoadStoreType: "
              << static_cast<int>(ctx->ldst_type) << std::endl;
    return;
  }
  while (iteration++ < pattern_iter) {
    func(addr, access_size, stride_size, delay, access_count, block_size,
         &latency_buf);
    latency += latency_buf / ((access_size / 0x40) * access_count);
    log.size += access_size * access_count;
    addr += stride_size * access_count;
    if (addr + access_size * access_count >= end_addr) {
      addr = ctx->addr;
    }
  }
  log.latency += latency / (iteration - 1);
  {
    std::lock_guard<std::mutex> lock(ctx->mutex);
    ctx->complete.notify_all();
  }
}

void SimpleLdStBandwidthPatternHandler::handle(
    std::shared_ptr<WorkerContext> ctx) {
  uint8_t *addr = ctx->addr;
  uint64_t size = ctx->size;
  uint64_t latency_buf = 0;
  BwPatternSize bw_pattern_size = ctx->ldst_type == LoadStoreType::LOAD
                                      ? ctx->bw_load_pattern_block_size
                                      : ctx->bw_store_pattern_block_size;
  WorkerTestLog &log = ctx->log;

  prepare(ctx);

  auto func = _simple_ldst_patterns.get(ctx->ldst_type);
  if (func == nullptr) {
    std::cerr << "Error: Invalid Simple LdSt Func for LoadStoreType: "
              << static_cast<int>(ctx->ldst_type) << std::endl;
    return;
  }

  while (true) {
    func(addr, size, &latency_buf, bw_pattern_size);
    log.latency += latency_buf;
    log.size += size;
    if (check_stop_condition(ctx)) {
      break;
    }
  };
}

void PointerChaseLatencyPatternHandler::handle(
    std::shared_ptr<WorkerContext> ctx) {
  uint64_t stride_size = ctx->lt_pattern_stride_size;
  uint64_t thread_buffer_size = ctx->size;
  uint64_t access_count = ctx->access_cnt;
  uint64_t block_size = ctx->lt_pattern_block_size;
  auto *addr = reinterpret_cast<uint64_t *>(ctx->addr);
  auto *end_addr = reinterpret_cast<uint64_t *>(ctx->end_addr);
  uint64_t latency = 0;
  WorkerTestLog &log = ctx->log;
  LoadStoreType ldst_type = ctx->ldst_type;
  uint32_t repeat_time = ctx->pattern_iteration;
  uint32_t thread_id = ctx->core_id;
  if (stride_size * access_count > thread_buffer_size) {
    access_count = thread_buffer_size / stride_size;
  }
  auto csize = thread_buffer_size / stride_size;
  prepare(ctx);

  auto *cindex = static_cast<uint64_t *>(malloc(csize * sizeof(uint64_t)));
  if (cindex == nullptr) {
    std::cerr << "Error: Failed to allocate memory for cindex" << std::endl;
    {
      std::lock_guard<std::mutex> lock(ctx->mutex);
      ctx->complete.notify_all();
    }
    exit(1);
  }

  auto *timing_load =
      static_cast<uint64_t *>(malloc(repeat_time * sizeof(uint64_t)));
  std::cout << "init chasing index" << std::endl;
  _pointer_chase_patterns.init_chasing_index(cindex, csize, thread_id);
  if (ctx->ldst_type == LoadStoreType::LOAD) {
    std::cout << "prepare pointer chaser" << std::endl;
    _pointer_chase_patterns.prepare_pointer_chaser(addr, end_addr, stride_size,
                                                   cindex, csize);
  }
  std::cout << "start pointer chaser" << std::endl;
  auto func = _pointer_chase_patterns.get(ctx->ldst_type);
  func(addr, thread_buffer_size, stride_size, 0, block_size, repeat_time,
       cindex, timing_load);
  std::cout << "end pointer chaser" << std::endl;
  for (unsigned long i = 0; i < repeat_time; i++) {
    latency += timing_load[i] / (thread_buffer_size / block_size);
  }
  log.latency = latency / (repeat_time);
  free(timing_load);
  {
    std::lock_guard<std::mutex> lock(ctx->mutex);
    ctx->complete.notify_all();
  }
}

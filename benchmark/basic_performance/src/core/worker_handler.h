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

#ifndef CXL_PERF_APP_DT_WORKER_HANDLER_H
#define CXL_PERF_APP_DT_WORKER_HANDLER_H
#include <core/data_structure.h>
#include <tasks/pattern_handler.h>
#include <utils/logger.h>

class WorkerHandler {
public:
  WorkerHandler();
  ~WorkerHandler();

  void initialize(const std::shared_ptr<JobInfo> &job_info, Logger &logger);
  virtual void start();
  virtual void wait();
  void wrap_up();
  [[nodiscard]] std::shared_ptr<WorkerInfo> get_worker_info() const;
  static void work(std::shared_ptr<WorkerContext> ctx);
  static void set_thread_affinity(std::thread &worker, std::size_t core_id,
                                  uint32_t thread_id);
  virtual void assign_handler(int thread_num,
                              std::shared_ptr<WorkerContext> ctx) = 0;
  virtual void report(Logger &logger) = 0;

private:
  std::shared_ptr<WorkerInfo> _worker_info;
  std::size_t get_core_number(int thread_num, SocketId socket_id);
  std::string generate_test_info(const std::shared_ptr<JobInfo> &job_info);
};

class WorkerHandlerForBandwidth : public WorkerHandler {
public:
  WorkerHandlerForBandwidth();
  ~WorkerHandlerForBandwidth() = default;
  void wait() override;
  void assign_handler(int thread_num, std::shared_ptr<WorkerContext> ctx) final;
  void report(Logger &logger) override;

private:
  std::shared_ptr<StrideBandwidthPatternHandler> _stride_bw_handler;
  std::shared_ptr<SimpleLdStBandwidthPatternHandler> _simple_bw_handler;
  std::unordered_map<BwPattern, std::shared_ptr<PatternHandler>>
      _bw_pattern_handler_map;
};

class WorkerHandlerForLatency : public WorkerHandler {
public:
  WorkerHandlerForLatency();
  ~WorkerHandlerForLatency() = default;
  void assign_handler(int thread_num, std::shared_ptr<WorkerContext> ctx) final;
  void report(Logger &logger) override;

private:
  std::shared_ptr<StrideLatencyPatternHandler> _stride_latency_handler;
  std::shared_ptr<PointerChaseLatencyPatternHandler>
      _pointer_chase_latency_handler;
  std::unordered_map<LatencyPattern, std::shared_ptr<PatternHandler>>
      _latency_pattern_handler_map;
};

class WorkerHandlerForBwVsLatency : public WorkerHandler {
public:
  WorkerHandlerForBwVsLatency();
  ~WorkerHandlerForBwVsLatency() = default;
  void wait() override;
  void assign_handler(int thread_num, std::shared_ptr<WorkerContext> ctx) final;
  void report(Logger &logger) override;

private:
  std::shared_ptr<StrideLatencyPatternHandler> _stride_latency_handler;
  std::shared_ptr<SimpleLdStBandwidthPatternHandler> _simple_bw_handler;
  std::shared_ptr<PointerChaseLatencyPatternHandler>
      _pointer_chase_latency_handler;
  std::shared_ptr<StrideBandwidthPatternHandler> _stride_bw_handler;
  std::unordered_map<LatencyPattern, std::shared_ptr<PatternHandler>>
      _latency_pattern_handler_map;
  std::unordered_map<BwPattern, std::shared_ptr<PatternHandler>>
      _bw_pattern_handler_map;
};

#endif // CXL_PERF_APP_DT_WORKER_HANDLER_H

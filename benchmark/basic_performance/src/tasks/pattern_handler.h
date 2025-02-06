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

#ifndef CXL_PERF_APP_DT_PATTERN_HANDLER_H
#define CXL_PERF_APP_DT_PATTERN_HANDLER_H
#include <core/data_structure.h>
#include <machine/machine_dependency.h>
#include <tasks/pointer_chase_patterns.h>
#include <tasks/simple_ldst_patterns.h>
#include <tasks/stride_patterns.h>

class PatternHandler {
public:
  virtual ~PatternHandler() = default;
  virtual void handle(std::shared_ptr<WorkerContext> ctx) = 0;

  void prepare(const std::shared_ptr<WorkerContext> &ctx);
  void wrapup();
  static bool check_stop_condition(const std::shared_ptr<WorkerContext> &ctx);

private:
  MemUtils _mem_utils;
};

class StrideLatencyPatternHandler : public PatternHandler {
public:
  StrideLatencyPatternHandler() = default;
  ~StrideLatencyPatternHandler() override = default;

  void handle(std::shared_ptr<WorkerContext> ctx) override;

private:
  StridePattern _stride_pattern;
};

class StrideBandwidthPatternHandler : public PatternHandler {
public:
  StrideBandwidthPatternHandler() = default;
  ~StrideBandwidthPatternHandler() override = default;

  void handle(std::shared_ptr<WorkerContext> ctx) override;

private:
  StridePattern _stride_pattern;
};

class SimpleLdStBandwidthPatternHandler : public PatternHandler {
public:
  SimpleLdStBandwidthPatternHandler() = default;
  ~SimpleLdStBandwidthPatternHandler() override = default;

  void handle(std::shared_ptr<WorkerContext> ctx) override;

private:
  SimpleLdStPatterns _simple_ldst_patterns;
};

class PointerChaseLatencyPatternHandler : public PatternHandler {
public:
  PointerChaseLatencyPatternHandler() = default;
  ~PointerChaseLatencyPatternHandler() override = default;

  void handle(std::shared_ptr<WorkerContext> ctx) override;

private:
  PointerChasePatternsAbstract _pointer_chase_patterns;
};
#endif // CXL_PERF_APP_DT_PATTERN_HANDLER_H

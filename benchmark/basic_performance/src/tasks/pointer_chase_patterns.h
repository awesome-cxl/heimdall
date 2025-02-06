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

#ifndef CXL_PERF_APP_DT_POINTER_CHASE_PATTERNS_H
#define CXL_PERF_APP_DT_POINTER_CHASE_PATTERNS_H
#include <core/system_define.h>
#include <cstdint>
#include <functional>

using PcLdSTFunc = std::function<void(
    uint64_t *base_addr, uint64_t region_size, uint64_t stride_size,
    uint64_t region_skip, uint64_t block_size, uint64_t repeat,
    uint64_t *cindex, uint64_t *timing)>;

class PointerChasePatternsAbstract {
public:
  PointerChasePatternsAbstract();
  ~PointerChasePatternsAbstract() = default;

  PcLdSTFunc get(LoadStoreType ldst_type);

  int init_chasing_index(uint64_t *cindex, uint64_t csize, uint32_t thread_id);
  void prepare_pointer_chaser(uint64_t *base_addr, uint64_t *end_addr,
                              uint64_t stride_size, uint64_t *cindex,
                              uint64_t csize);

private:
  std::unordered_map<LoadStoreType, PcLdSTFunc> _func_map;
  CHASING_TYPE _chasing_type;
  void load(uint64_t *base_addr, uint64_t region_size, uint64_t stride_size,
            uint64_t region_skip, uint64_t block_size, uint64_t repeat,
            uint64_t *cindex, uint64_t *timing_load);
  void store(uint64_t *base_addr, uint64_t region_size, uint64_t stride_size,
             uint64_t region_skip, uint64_t block_size, uint64_t repeat,
             uint64_t *cindex, uint64_t *timing_store);
  std::string get_filename(uint64_t csize, uint32_t thread_id);
  bool load_from_file(uint64_t *cindex, uint64_t csize, uint32_t thread_id);
  void save_to_file(const uint64_t *cindex, uint64_t csize, uint32_t thread_id);
};

#endif // CXL_PERF_APP_DT_POINTER_CHASE_PATTERNS_H

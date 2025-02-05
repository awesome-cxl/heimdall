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

#include <machine/machine_dependency.h>
#include <tasks/simple_ldst_patterns.h>

SimpleLdStPatterns::SimpleLdStPatterns() {
  _func_map[LoadStoreType::LOAD] = [this](uint8_t *addr, uint64_t size,
                                          uint64_t *latency_buf,
                                          BwPatternSize pattern_size) {
    this->load(addr, size, latency_buf, pattern_size);
  };
  _func_map[LoadStoreType::STORE] = [this](uint8_t *addr, uint64_t size,
                                           uint64_t *latency_buf,
                                           BwPatternSize pattern_size) {
    this->store(addr, size, latency_buf, pattern_size);
  };
};

SimpleLdStPatterns::~SimpleLdStPatterns() {}

SLdStFunc SimpleLdStPatterns::get(LoadStoreType type) {
  auto it = _func_map.find(type);
  if (it == _func_map.end()) {
    std::cerr << "Can not find the function for the given type" << std::endl;
  }
  return it->second;
}

void SimpleLdStPatterns::load(uint8_t *addr, uint64_t size,
                              uint64_t *latency_buf,
                              BwPatternSize pattern_size) {
  Timer timer;
  LdStPattern pattern;
  *latency_buf = 0;
  timer.start();
  auto func = pattern.get_load_func(pattern_size);
  func(addr, size);
  *latency_buf = timer.elapsed();
}

void SimpleLdStPatterns::store(uint8_t *addr, uint64_t size,
                               uint64_t *latency_buf,
                               BwPatternSize pattern_size) {
  Timer timer;
  LdStPattern pattern;
  *latency_buf = 0;
  auto func = pattern.get_store_func(pattern_size);
  timer.start();
  func(addr, size);
  *latency_buf = timer.elapsed();
}

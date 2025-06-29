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

#include <cstring>
#include <fstream>
#include <iostream>
#include <machine/machine_dependency.h>
#include <random>
#include <tasks/pointer_chase_patterns.h>
#include <thread>
#include <utils/timer.h>

PointerChasePatternsAbstract::PointerChasePatternsAbstract()
    : _chasing_type(CHASING_TYPE::CHASING_TYPE_RANDOM) {
  _func_map[LoadStoreType::LOAD] =
      [this](uint64_t *base_addr, uint64_t region_size, uint64_t stride_size,
             uint64_t region_skip, uint64_t block_size, uint64_t repeat,
             uint64_t *cindex, uint64_t *timing_load) {
        this->load(base_addr, region_size, stride_size, region_skip, block_size,
                   repeat, cindex, timing_load);
      };
  _func_map[LoadStoreType::STORE] =
      [this](uint64_t *base_addr, uint64_t region_size, uint64_t stride_size,
             uint64_t region_skip, uint64_t block_size, uint64_t repeat,
             uint64_t *cindex, uint64_t *timing_store) {
        this->store(base_addr, region_size, stride_size, region_skip,
                    block_size, repeat, cindex, timing_store);
      };
}

void PointerChasePatternsAbstract::load(
    uint64_t *base_addr, uint64_t region_size, uint64_t stride_size,
    uint64_t region_skip, uint64_t block_size, uint64_t repeat,
    uint64_t *cindex, uint64_t *timing_load) {
  int i = 0;
  Timer timer;
  MemUtils util;
  for (i = 0; i < repeat; i++) {
    PointerChaseLdStPattern::load_64B(base_addr, region_size, stride_size,
                                      block_size, &timing_load[i], timer);
  }
}
#pragma GCC push_options
#pragma GCC optimize("O0")
void PointerChasePatternsAbstract::store(
    uint64_t *base_addr, uint64_t region_size, uint64_t stride_size,
    uint64_t region_skip, uint64_t block_size, uint64_t repeat,
    uint64_t *cindex, uint64_t *timing_store) {
  int i = 0;
  Timer timer;
  MemUtils util;
  for (i = 0; i < repeat; i++) {
    PointerChaseLdStPattern::store_64B(base_addr, region_size, stride_size,
                                       block_size, cindex, &timing_store[i],
                                       timer);
  }
}
#pragma GCC pop_options

std::string PointerChasePatternsAbstract::get_filename(uint64_t csize,
                                                       uint32_t thread_id) {
  return "pointer_chase_" + std::to_string(thread_id) + "_" +
         std::to_string(csize) + ".txt";
}

bool PointerChasePatternsAbstract::load_from_file(uint64_t *cindex,
                                                  uint64_t csize,
                                                  uint32_t thread_id) {
  std::ifstream infile(get_filename(csize, thread_id));
  if (!infile)
    return false;

  for (uint64_t i = 0; i < csize; ++i) {
    if (!(infile >> cindex[i])) {
      return false;
    }
  }

  std::cout << "Loaded pointer chase index from file.\n";
  return true;
}

void PointerChasePatternsAbstract::save_to_file(const uint64_t *cindex,
                                                uint64_t csize,
                                                uint32_t thread_id) {
  std::ofstream outfile(get_filename(csize, thread_id));
  for (uint64_t i = 0; i < csize; ++i) {
    outfile << cindex[i] << "\n";
  }
  std::cout << "Saved pointer chase index to file.\n";
}

int PointerChasePatternsAbstract::init_chasing_index(uint64_t *cindex,
                                                     uint64_t csize,
                                                     uint32_t thread_id) {
  memset(cindex, 0, sizeof(uint64_t) * csize);

  if (load_from_file(cindex, csize, thread_id)) {
    return 0;
  }

  uint64_t curr_pos = 0;
  uint64_t next_pos = 0;
  std::vector<bool> used(csize, false);

  static thread_local std::mt19937_64 gen(std::random_device{}());

  for (uint64_t i = 0; i < csize - 1; i++) {
    if (_chasing_type == CHASING_TYPE::CHASING_TYPE_RANDOM) {
      do {
        next_pos = std::uniform_int_distribution<uint64_t>(0, csize - 1)(gen);
      } while (used[next_pos] || next_pos == curr_pos);

      used[next_pos] = true;
    } else {
      next_pos = curr_pos + 1; // Sequential chasing
    }

    cindex[curr_pos] = next_pos;
    curr_pos = next_pos;
  }

  save_to_file(cindex, csize, thread_id);
  return 0;
}

void PointerChasePatternsAbstract::prepare_pointer_chaser(uint64_t *base_addr,
                                                          uint64_t *end_add,
                                                          uint64_t stride_size,
                                                          uint64_t *cindex,
                                                          uint64_t csize) {
  uint64_t curr_pos = 0;
  uint64_t next_pos = 0;
  const auto start_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                            std::chrono::system_clock::now().time_since_epoch())
                            .count();
  for (auto i = 0; i < csize - 1; i++) {
    if (curr_pos >= csize) [[unlikely]] {
      std::cerr << "Error: curr_pos >= csize" << std::endl;
      return;
    }
    uint64_t *curr_addr = base_addr + curr_pos * stride_size / sizeof(uint64_t);
    if (curr_addr >= end_add) [[unlikely]] {
      std::cout << "curr_pos: " << curr_pos << std::endl;
      std::cout << "stride size: " << stride_size << std::endl;
      std::cout << "curr_addr: " << curr_addr << std::endl;
      std::cout << "end_addr: " << end_add << std::endl;
      std::cerr << "Error: curr_addr >= end_add" << std::endl;
      return;
    }
    next_pos = cindex[curr_pos];
    *curr_addr = next_pos;
    curr_pos = next_pos;

    // Check for timeout
    if (rand() % 10000 == 0) [[unlikely]] {
      const auto curr_ms =
          std::chrono::duration_cast<std::chrono::milliseconds>(
              std::chrono::system_clock::now().time_since_epoch())
              .count();
      if (curr_ms - start_ms > 2 * 60 * 1000) { // 2 minutes
        std::cerr << "Pointer chasing timed out" << std::endl;
        return;
      }
    }
  }
}

PcLdSTFunc PointerChasePatternsAbstract::get(LoadStoreType ldst_type) {
  auto it = _func_map.find(ldst_type);
  if (it == _func_map.end()) {
    std::cerr << "Error: LoadStoreType not found" << std::endl;
    return nullptr;
  }
  return it->second;
}

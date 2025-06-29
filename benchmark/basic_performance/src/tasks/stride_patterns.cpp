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

#include <iostream>
#include <machine/machine_dependency.h>
#include <tasks/stride_patterns.h>

StridePattern::StridePattern() {
  _func_map[LoadStoreType::LOAD] =
      [this](uint8_t *start_addr, uint64_t size, uint64_t skip, uint64_t delay,
             uint64_t count, uint64_t block_size, uint64_t *time_log) {
        this->stride_load(start_addr, size, skip, delay, count, block_size,
                          time_log);
      };
  _func_map[LoadStoreType::LOAD_WITH_FLUSH] =
      [this](uint8_t *start_addr, uint64_t size, uint64_t skip, uint64_t delay,
             uint64_t count, uint64_t block_size, uint64_t *time_log) {
        this->stride_load_with_flush(start_addr, size, skip, delay, count,
                                     block_size, time_log);
      };
  _func_map[LoadStoreType::STORE] =
      [this](uint8_t *start_addr, uint64_t size, uint64_t skip, uint64_t delay,
             uint64_t count, uint64_t block_size, uint64_t *time_log) {
        this->stride_store(start_addr, size, skip, delay, count, block_size,
                           time_log);
      };
  _func_map[LoadStoreType::STORE_WITH_FLUSH] =
      [this](uint8_t *start_addr, uint64_t size, uint64_t skip, uint64_t delay,
             uint64_t count, uint64_t block_size, uint64_t *time_log) {
        this->stride_store_with_flush(start_addr, size, skip, delay, count,
                                      block_size, time_log);
      };
}

StrideFunc StridePattern::get(LoadStoreType type) {
  auto it = _func_map.find(type);
  if (it == _func_map.end()) {
    std::cerr << "Invalid LoadStoreType" << std::endl;
  }
  return it->second;
}

void StridePattern::stride_load(uint8_t *start_addr, uint64_t size,
                                uint64_t skip, uint64_t delay, uint64_t count,
                                uint64_t block_size, uint64_t *time_log) {
  Timer timer;
  long i = 0, offset = 0;
  _func = get_load_func(block_size);
  *time_log = 0;
  timer.start();
  while (i < count) {
    uint8_t *test_addr = start_addr + offset;
    _func(test_addr, size);
    offset += skip;
    i++;
  }
  *time_log = timer.elapsed();
}

void StridePattern::stride_load_with_flush(uint8_t *start_addr, uint64_t size,
                                           uint64_t skip, uint64_t delay,
                                           uint64_t count, uint64_t block_size,
                                           uint64_t *time_log) {
  long i = 0, offset = 0;
  Timer timer;
  *time_log = 0;
  while (i < count) {
    uint8_t *test_addr = start_addr + offset;
    LdStPattern::load_with_flush(test_addr, size, time_log, timer);
    offset += skip;
    i++;
  }
}

void StridePattern::stride_store(uint8_t *start_addr, uint64_t size,
                                 uint64_t skip, uint64_t delay, uint64_t count,
                                 uint64_t block_size, uint64_t *time_log) {
  Timer timer;
  long i = 0, offset = 0;
  _func = get_store_func(block_size);
  *time_log = 0;
  timer.start();
  while (i < count) {
    uint8_t *test_addr = start_addr + offset;
    _func(test_addr, size);
    offset += skip;
    i++;
  }
  *time_log = timer.elapsed();
}

void StridePattern::stride_store_with_flush(uint8_t *start_addr, uint64_t size,
                                            uint64_t skip, uint64_t delay,
                                            uint64_t count, uint64_t block_size,
                                            uint64_t *time_log) {
  long i = 0, offset = 0;
  Timer timer;
  *time_log = 0;
  while (i < count) {
    uint8_t *test_addr = start_addr + offset;
    LdStPattern::store_with_flush(test_addr, size, time_log, timer);
    offset += skip;
    i++;
  }
}

LdStFunc StridePattern::get_load_func(uint64_t block_size) {
  if (block_size == BlockSize::BLOCK_64B) {
    return [this](uint8_t *addr, uint64_t size) {
      LdStPattern::load_64B(addr, size);
    };
  } else if (block_size == BlockSize::BLOCK_128B) {
    return [this](uint8_t *addr, uint64_t size) {
      LdStPattern::load_128B(addr, size);
    };
  } else if (block_size == BlockSize::BLOCK_256B) {
    return [this](uint8_t *addr, uint64_t size) {
      LdStPattern::load_256B(addr, size);
    };
  } else if (block_size == BlockSize::BLOCK_512B) {
    return [this](uint8_t *addr, uint64_t size) {
      LdStPattern::load_512B(addr, size);
    };
  } else {
    throw std::invalid_argument("Invalid block size");
  }
}

LdStFunc StridePattern::get_store_func(uint64_t block_size) {
  if (block_size == BlockSize::BLOCK_64B) {
    return [this](uint8_t *addr, uint64_t size) {
      LdStPattern::store_64B(addr, size);
    };
  } else if (block_size == BlockSize::BLOCK_128B) {
    return [this](uint8_t *addr, uint64_t size) {
      LdStPattern::store_128B(addr, size);
    };
  } else if (block_size == BlockSize::BLOCK_256B) {
    return [this](uint8_t *addr, uint64_t size) {
      LdStPattern::store_256B(addr, size);
    };
  } else if (block_size == BlockSize::BLOCK_512B) {
    return [this](uint8_t *addr, uint64_t size) {
      LdStPattern::store_512B(addr, size);
    };
  } else {
    throw std::invalid_argument("Invalid block size");
  }
}

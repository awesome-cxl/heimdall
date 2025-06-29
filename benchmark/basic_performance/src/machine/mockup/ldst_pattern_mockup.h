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

#ifndef CXL_PERF_APP_DT_LDST_PATTERN_MOCKUP_H
#define CXL_PERF_APP_DT_LDST_PATTERN_MOCKUP_H
#include <cstring>
#include <utils/timer.h>

class LdStPattern {
public:
  LdStPattern() = default;
  ~LdStPattern() = default;

  static inline void load_64B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    volatile char buffer[64];
    while (size_cnt < size) {
      std::memcpy((void *)buffer, (void *)(addr + size_cnt), sizeof(buffer));
      size_cnt += sizeof(buffer);
    }
  }

  static inline void load_128B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    volatile char buffer[128];
    while (size_cnt < size) {
      std::memcpy((void *)buffer, (void *)(addr + size_cnt), sizeof(buffer));
      size_cnt += sizeof(buffer);
    }
  }

  static inline void load_256B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    volatile char buffer[256];
    while (size_cnt < size) {
      std::memcpy((void *)buffer, (void *)(addr + size_cnt), sizeof(buffer));
      size_cnt += sizeof(buffer);
    }
  }

  static inline void load_512B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    volatile char buffer[512];
    while (size_cnt < size) {
      std::memcpy((void *)buffer, (void *)(addr + size_cnt), sizeof(buffer));
      size_cnt += sizeof(buffer);
    }
  }

  static inline void load_with_flush(uint8_t *addr, uint64_t size,
                                     uint64_t *time_log, Timer &timer) {
    long size_cnt = 0;
    volatile char buffer[64]; // 64-byte buffer to simulate cache line access
    while (size_cnt < size) {
      timer.start();
      std::memcpy((void *)buffer, (void *)(addr + size_cnt), sizeof(buffer));
      *time_log += timer.elapsed();
      std::memset((void *)(addr + size_cnt), 0, sizeof(buffer));
      size_cnt += sizeof(buffer);
    }
  }

  static inline void store_64B(uint8_t *addr, uint64_t size) {
    std::cout << "mockup store_64B" << std::endl;
    long size_cnt = 0;
    volatile char buffer[64] = {0}; // 64-byte buffer initialized with zeros
    while (size_cnt < size) {
      std::memcpy((void *)(addr + size_cnt), (void *)buffer, sizeof(buffer));
      size_cnt += sizeof(buffer);
    }
  }

  static inline void store_128B(uint8_t *addr, uint64_t size) {
    std::cout << "mockup store_128B" << std::endl;
    long size_cnt = 0;
    volatile char buffer[128] = {0}; // 128-byte buffer initialized with zeros
    while (size_cnt < size) {
      std::memcpy((void *)(addr + size_cnt), (void *)buffer, sizeof(buffer));
      size_cnt += sizeof(buffer);
    }
  }

  static inline void store_256B(uint8_t *addr, uint64_t size) {
    std::cout << "mockup store_256B" << std::endl;
    long size_cnt = 0;
    volatile char buffer[256] = {0}; // 256-byte buffer initialized with zeros
    while (size_cnt < size) {
      std::memcpy((void *)(addr + size_cnt), (void *)buffer, sizeof(buffer));
      size_cnt += sizeof(buffer);
    }
  }

  static inline void store_512B(uint8_t *addr, uint64_t size) {
    std::cout << "mockup store_512B" << std::endl;
    long size_cnt = 0;
    volatile char buffer[512] = {0}; // 512-byte buffer initialized with zeros
    while (size_cnt < size) {
      std::memcpy((void *)(addr + size_cnt), (void *)buffer, sizeof(buffer));
      size_cnt += sizeof(buffer);
    }
  }

  static inline void store_with_flush(uint8_t *addr, uint64_t size,
                                      uint64_t *time_log, Timer &timer) {
    std::cout << "mockup store_with_flush" << std::endl;
    long size_cnt = 0;
    volatile char buffer[64] = {0}; // 64-byte buffer initialized with zeros
    while (size_cnt < size) {
      timer.start();
      std::memcpy((void *)(addr + size_cnt), (void *)buffer, sizeof(buffer));
      *time_log += timer.elapsed();
      std::memset((void *)(addr + size_cnt), 0,
                  sizeof(buffer)); // Clear the written memory
      size_cnt += sizeof(buffer);
    }
  }
};
#endif // CXL_PERF_APP_DT_LDST_PATTERN_MOCKUP_H

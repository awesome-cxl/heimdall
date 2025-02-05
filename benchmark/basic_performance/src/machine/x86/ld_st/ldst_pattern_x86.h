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

#ifndef CXL_PERF_APP_ACCESS_PATTERN_X86_H
#define CXL_PERF_APP_ACCESS_PATTERN_X86_H
#include <core/system_define.h>
#include <cstring>
#include <functional>
#include <machine/x86/ld_st/mem_utils_x86.h>
#include <unordered_map>
#include <utils/timer.h>
using LdStPatternFunc = std::function<void(uint8_t *addr, uint64_t size)>;

class LdStPattern {
public:
  LdStPattern() {
    _ld_func_map[BwPatternSize::SIZE_64B] = load_64B;
    _ld_func_map[BwPatternSize::SIZE_128B] = load_128B;
    _ld_func_map[BwPatternSize::SIZE_256B] = load_256B;
    _ld_func_map[BwPatternSize::SIZE_512B] = load_512B;
    _st_func_map[BwPatternSize::SIZE_64B] = store_64B;
    _st_func_map[BwPatternSize::SIZE_128B] = store_128B;
    _st_func_map[BwPatternSize::SIZE_256B] = store_256B;
    _st_func_map[BwPatternSize::SIZE_512B] = store_512B;
  }
  ~LdStPattern() = default;

  LdStPatternFunc get_load_func(BwPatternSize type) {
    auto it = _ld_func_map.find(type);
    if (it == _ld_func_map.end()) {
      std::cerr << "Can not find the function for the given type" << std::endl;
    }
    return it->second;
  }

  LdStPatternFunc get_store_func(BwPatternSize type) {
    auto it = _st_func_map.find(type);
    if (it == _st_func_map.end()) {
      std::cerr << "Can not find the function for the given type" << std::endl;
    }
    return it->second;
  }

  static inline void load_64B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("vmovntdqa (%0),%%zmm0\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "zmm0", "memory");
      size_cnt += 0x40;
    }
  }

  static inline void load_128B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("vmovntdqa  0x0(%0), %%zmm0\n\t"
                   "vmovntdqa  0x40(%0), %%zmm1\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "zmm0", "zmm1", "memory");
      size_cnt += 0x80;
    }
  }

  static inline void load_256B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("vmovntdqa  0x0(%0), %%zmm0\n\t"
                   "vmovntdqa  0x40(%0), %%zmm1\n\t"
                   "vmovntdqa  0x80(%0), %%zmm2\n\t"
                   "vmovntdqa  0xc0(%0), %%zmm3\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "zmm0", "zmm1", "zmm2", "zmm3", "memory");
      size_cnt += 0x100;
    }
  }

  static inline void load_512B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("vmovntdqa  0x0(%0), %%zmm0\n\t"
                   "vmovntdqa  0x40(%0), %%zmm1\n\t"
                   "vmovntdqa  0x80(%0), %%zmm2\n\t"
                   "vmovntdqa  0xc0(%0), %%zmm3\n\t"
                   "vmovntdqa  0x100(%0), %%zmm4\n\t"
                   "vmovntdqa  0x140(%0), %%zmm5\n\t"
                   "vmovntdqa  0x180(%0), %%zmm6\n\t"
                   "vmovntdqa  0x1c0(%0), %%zmm7\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "zmm0", "zmm1", "zmm2", "zmm3", "zmm4", "zmm5", "zmm6",
                     "zmm7", "memory");
      size_cnt += 0x200;
    }
  }

  static inline void load_with_flush(uint8_t *addr, uint64_t size,
                                     uint64_t *time_log, Timer &timer) {
    long size_cnt = 0;
    while (size_cnt < size) {
      timer.start();
      asm volatile("vmovntdqa (%0),%%zmm0\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "zmm0");
      *time_log += timer.elapsed();
      asm volatile("clflush 0(%0)" ::"r"(addr + size_cnt) : "memory");
      size_cnt += 0x40;
    }
  }

  static inline void store_64B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("vmovntdq %%zmm0, (%0)\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "memory");
      size_cnt += 0x40; // 64 bytes
    }
  }

  static inline void store_128B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("vmovntdq %%zmm0, 0x0(%0)\n\t"
                   "vmovntdq %%zmm1, 0x40(%0)\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "memory");
      size_cnt += 0x80; // 128 bytes
    }
  }

  static inline void store_256B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("vmovntdq %%zmm0, 0x0(%0)\n\t"
                   "vmovntdq %%zmm1, 0x40(%0)\n\t"
                   "vmovntdq %%zmm2, 0x80(%0)\n\t"
                   "vmovntdq %%zmm3, 0xc0(%0)\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "memory");
      size_cnt += 0x100; // 256 bytes
    }
  }

  static inline void store_512B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("vmovntdq %%zmm0, 0x0(%0)\n\t"
                   "vmovntdq %%zmm1, 0x40(%0)\n\t"
                   "vmovntdq %%zmm2, 0x80(%0)\n\t"
                   "vmovntdq %%zmm3, 0xc0(%0)\n\t"
                   "vmovntdq %%zmm4, 0x100(%0)\n\t"
                   "vmovntdq %%zmm5, 0x140(%0)\n\t"
                   "vmovntdq %%zmm6, 0x180(%0)\n\t"
                   "vmovntdq %%zmm7, 0x1c0(%0)\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "memory");
      size_cnt += 0x200; // 512 bytes
    }
  }

  static inline void store_with_flush(uint8_t *addr, uint64_t size,
                                      uint64_t *time_log, Timer &timer) {
    long size_cnt = 0;
    while (size_cnt < size) {
      timer.start();
      asm volatile("vmovntdq %%zmm0, (%0)\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "memory");
      *time_log += timer.elapsed();
      asm volatile("clflush (%0)\n\t" ::"r"(addr + size_cnt) : "memory");
      size_cnt += 0x40; // 64 bytes
    }
  }

private:
  std::unordered_map<BwPatternSize, LdStPatternFunc> _ld_func_map;
  std::unordered_map<BwPatternSize, LdStPatternFunc> _st_func_map;
};

class PointerChaseLdStPattern {
public:
  PointerChaseLdStPattern() = default;
  ~PointerChaseLdStPattern() = default;
#pragma GCC push_options
#pragma GCC optimize("O0")
  static inline void load_64B(uint64_t *base_addr, uint64_t region_size,
                              uint64_t stride_size, uint64_t block_size,
                              uint64_t *time_log, Timer &timer) {
    uint64_t scanned_size = 0;
    uint64_t curr_pos = 0;
    uint64_t next_pos = 0;
    *time_log = 0;
    MemUtils util;
    while (scanned_size < region_size) {
      uint64_t *curr_addr =
          base_addr + curr_pos * stride_size / sizeof(uint64_t);
      asm volatile("clflush 0(%0)" ::"r"(curr_addr) : "memory");
      asm volatile("mfence" ::: "memory");
      timer.start();
      asm volatile("mov (%1), %0\n\t"
                   : "=r"(next_pos)
                   : "r"(curr_addr)
                   : "memory");
      asm volatile("mfence" ::: "memory");
      *time_log += timer.elapsed();
      curr_pos = next_pos;
      scanned_size += block_size;
    }
  }
#pragma GCC pop_options

#pragma GCC push_options
#pragma GCC optimize("O0")
  static inline void store_64B(uint64_t *base_addr, uint64_t region_size,
                               uint64_t stride_size, uint64_t block_size,
                               uint64_t *cindex, uint64_t *time_log,
                               Timer &timer) {
    uint64_t scanned_size = 0;
    uint64_t curr_pos = 0;
    uint64_t next_pos = 0;
    *time_log = 0;
    MemUtils util;
    while (scanned_size < region_size) {
      uint64_t *curr_addr =
          base_addr + curr_pos * stride_size / sizeof(uint64_t);
      asm volatile("clflush 0(%0)" ::"r"(curr_addr) : "memory");
      asm volatile("mfence" ::: "memory");
      next_pos = cindex[curr_pos];
      timer.start();
      asm volatile("mov %1, (%0)\n\t"
                   :
                   : "r"(curr_addr), "r"(next_pos)
                   : "memory");
      asm volatile("mfence" ::: "memory");
      *time_log += timer.elapsed();
      asm volatile("clflush 0(%0)" ::"r"(curr_addr) : "memory");
      asm volatile("mfence" ::: "memory");
      curr_pos = next_pos;
      scanned_size += block_size;
    }
  }
#pragma GCC pop_options
};

#endif // CXL_PERF_APP_ACCESS_PATTERN_X86_H

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

#ifndef CXL_PERF_APP_DT_ACCESS_PATTERN_ARM_H
#define CXL_PERF_APP_DT_ACCESS_PATTERN_ARM_H

#include <cstring>
#include <iostream>
#include <machine/arm/mem_utils_arm.h>
#include <utils/timer.h>

class LdStPattern {
public:
  LdStPattern() = default;

  ~LdStPattern() = default;

  static inline void load_64B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("LDNP q0, q1, [%0]\n\t"
                   "LDNP q2, q3, [%0, #32]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "memory");
      asm volatile("dmb sy" : : : "memory");
      size_cnt += 0x40;
    }
  }

  static inline void load_128B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("LDNP q0, q1, [%0]\n\t"
                   "LDNP q2, q3, [%0, #32]\n\t"
                   "LDNP q4, q5, [%0, #64]\n\t"
                   "LDNP q6, q7, [%0, #96]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "memory");
      asm volatile("dmb sy" : : : "memory");
      size_cnt += 0x80;
    }
  }

  static inline void load_256B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("LDNP q0, q1, [%0]\n\t"
                   "LDNP q2, q3, [%0, #32]\n\t"
                   "LDNP q4, q5, [%0, #64]\n\t"
                   "LDNP q6, q7, [%0, #96]\n\t"
                   "LDNP q8, q9, [%0, #128]\n\t"
                   "LDNP q10, q11, [%0, #160]\n\t"
                   "LDNP q12, q13, [%0, #192]\n\t"
                   "LDNP q14, q15, [%0, #224]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9",
                     "q10", "q11", "q12", "q13", "q14", "q15", "memory");
      asm volatile("dmb sy" : : : "memory");
      size_cnt += 0x100;
    }
  }

  static inline void load_512B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("LDNP q0, q1, [%0]\n\t"
                   "LDNP q2, q3, [%0, #32]\n\t"
                   "LDNP q4, q5, [%0, #64]\n\t"
                   "LDNP q6, q7, [%0, #96]\n\t"
                   "LDNP q8, q9, [%0, #128]\n\t"
                   "LDNP q10, q11, [%0, #160]\n\t"
                   "LDNP q12, q13, [%0, #192]\n\t"
                   "LDNP q14, q15, [%0, #224]\n\t"
                   "LDNP q16, q17, [%0, #256]\n\t"
                   "LDNP q18, q19, [%0, #288]\n\t"
                   "LDNP q20, q21, [%0, #320]\n\t"
                   "LDNP q22, q23, [%0, #352]\n\t"
                   "LDNP q24, q25, [%0, #384]\n\t"
                   "LDNP q26, q27, [%0, #416]\n\t"
                   "LDNP q28, q29, [%0, #448]\n\t"
                   "LDNP q30, q31, [%0, #480]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9",
                     "q10", "q11", "q12", "q13", "q14", "q15", "q16", "q17",
                     "q18", "q19", "q20", "q21", "q22", "q23", "q24", "q25",
                     "q26", "q27", "q28", "q29", "q30", "q31", "memory");
      asm volatile("dmb sy" : : : "memory");
      size_cnt += 0x200; // 512 bytes (0x200 in hexadecimal)
    }
  }

  static inline void load_with_flush(uint8_t *addr, uint64_t size,
                                     uint64_t *time_log, Timer &timer) {
    long size_cnt = 0;
    while (size_cnt < size) {
      timer.start();
      asm volatile("LDNP q0, q1, [%0]\n\t"
                   "LDNP q2, q3, [%0, #32]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "memory");
      asm volatile("dmb sy" : : : "memory");
      *time_log += timer.elapsed();
      asm volatile("dc civac, %[addr]\n\t"
                   :
                   : [addr] "r"(addr + size_cnt)
                   : "memory");
      size_cnt += 0x40;
    }
  }

  static inline void store_64B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("STNP q0, q1, [%0]\n\t"
                   "STNP q2, q3, [%0, #32]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "memory");
      size_cnt += 0x40;
    }
  }

  static inline void store_128B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("STNP q0, q1, [%0]\n\t"
                   "STNP q2, q3, [%0, #32]\n\t"
                   "STNP q4, q5, [%0, #64]\n\t"
                   "STNP q6, q7, [%0, #96]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "memory");
      size_cnt += 0x80;
    }
  }

  static inline void store_256B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("STNP q0, q1, [%0]\n\t"
                   "STNP q2, q3, [%0, #32]\n\t"
                   "STNP q4, q5, [%0, #64]\n\t"
                   "STNP q6, q7, [%0, #96]\n\t"
                   "STNP q8, q9, [%0, #128]\n\t"
                   "STNP q10, q11, [%0, #160]\n\t"
                   "STNP q12, q13, [%0, #192]\n\t"
                   "STNP q14, q15, [%0, #224]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9",
                     "q10", "q11", "q12", "q13", "q14", "q15", "memory");
      size_cnt += 0x100;
    }
  }

  static inline void store_512B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("STNP q0, q1, [%0]\n\t"
                   "STNP q2, q3, [%0, #32]\n\t"
                   "STNP q4, q5, [%0, #64]\n\t"
                   "STNP q6, q7, [%0, #96]\n\t"
                   "STNP q8, q9, [%0, #128]\n\t"
                   "STNP q10, q11, [%0, #160]\n\t"
                   "STNP q12, q13, [%0, #192]\n\t"
                   "STNP q14, q15, [%0, #224]\n\t"
                   "STNP q16, q17, [%0, #256]\n\t"
                   "STNP q18, q19, [%0, #288]\n\t"
                   "STNP q20, q21, [%0, #320]\n\t"
                   "STNP q22, q23, [%0, #352]\n\t"
                   "STNP q24, q25, [%0, #384]\n\t"
                   "STNP q26, q27, [%0, #416]\n\t"
                   "STNP q28, q29, [%0, #448]\n\t"
                   "STNP q30, q31, [%0, #480]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9",
                     "q10", "q11", "q12", "q13", "q14", "q15", "q16", "q17",
                     "q18", "q19", "q20", "q21", "q22", "q23", "q24", "q25",
                     "q26", "q27", "q28", "q29", "q30", "q31", "memory");
      size_cnt += 0x200;
    }
  }

  static inline void store_1024B(uint8_t *addr, uint64_t size) {
    long size_cnt = 0;
    while (size_cnt < size) {
      asm volatile("STNP q0, q1, [%0]\n\t"
                   "STNP q2, q3, [%0, #32]\n\t"
                   "STNP q4, q5, [%0, #64]\n\t"
                   "STNP q6, q7, [%0, #96]\n\t"
                   "STNP q8, q9, [%0, #128]\n\t"
                   "STNP q10, q11, [%0, #160]\n\t"
                   "STNP q12, q13, [%0, #192]\n\t"
                   "STNP q14, q15, [%0, #224]\n\t"
                   "STNP q16, q17, [%0, #256]\n\t"
                   "STNP q18, q19, [%0, #288]\n\t"
                   "STNP q20, q21, [%0, #320]\n\t"
                   "STNP q22, q23, [%0, #352]\n\t"
                   "STNP q24, q25, [%0, #384]\n\t"
                   "STNP q26, q27, [%0, #416]\n\t"
                   "STNP q28, q29, [%0, #448]\n\t"
                   "STNP q30, q31, [%0, #480]\n\t"
                   "STNP q0, q1, [%0, #512]\n\t"
                   "STNP q2, q3, [%0, #544]\n\t"
                   "STNP q4, q5, [%0, #576]\n\t"
                   "STNP q6, q7, [%0, #608]\n\t"
                   "STNP q8, q9, [%0, #640]\n\t"
                   "STNP q10, q11, [%0, #672]\n\t"
                   "STNP q12, q13, [%0, #704]\n\t"
                   "STNP q14, q15, [%0, #736]\n\t"
                   "STNP q16, q17, [%0, #768]\n\t"
                   "STNP q18, q19, [%0, #800]\n\t"
                   "STNP q20, q21, [%0, #832]\n\t"
                   "STNP q22, q23, [%0, #864]\n\t"
                   "STNP q24, q25, [%0, #896]\n\t"
                   "STNP q26, q27, [%0, #928]\n\t"
                   "STNP q28, q29, [%0, #960]\n\t"
                   "STNP q30, q31, [%0, #992]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9",
                     "q10", "q11", "q12", "q13", "q14", "q15", "q16", "q17",
                     "q18", "q19", "q20", "q21", "q22", "q23", "q24", "q25",
                     "q26", "q27", "q28", "q29", "q30", "q31", "memory");
      size_cnt += 0x400;
    }
  }

  static inline void store_with_flush(uint8_t *addr, uint64_t size,
                                      uint64_t *time_log, Timer &timer) {
    long size_cnt = 0;
    while (size_cnt < size) {
      timer.start();
      asm volatile("STNP q0, q1, [%0]\n\t"
                   "STNP q2, q3, [%0, #32]\n\t"
                   :
                   : "r"(addr + size_cnt)
                   : "q0", "q1", "q2", "q3", "memory");
      asm volatile("dmb sy" : : : "memory");
      *time_log += timer.elapsed();
      asm volatile("dc civac, %[addr]\n\t"
                   :
                   : [addr] "r"(addr + size_cnt)
                   : "memory");
      size_cnt += 0x40;
    }
  }
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
      asm volatile("dc civac, %0" ::"r"(curr_addr) : "memory");
      asm volatile("dsb sy" ::: "memory");
      timer.start();
      asm volatile("LDNP x0, x1, [%1]\n\t"
                   "MOV %0, x0\n\t"
                   : "=r"(next_pos)
                   : "r"(curr_addr)
                   : "x0", "x1", "memory");
      /*
      asm volatile (
          "ldr %0, [%1]\n\t"
          : "=r"(next_pos)
          : "r"(curr_addr)
          : "memory"
      );
      */
      asm volatile("dsb sy" ::: "memory");
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
      asm volatile("dc civac, %0" ::"r"(curr_addr) : "memory");
      asm volatile("dsb sy" ::: "memory");
      next_pos = cindex[curr_pos];
      timer.start();
      asm volatile("STNP x1, x1, [%0]\n\t"
                   :
                   : "r"(curr_addr), "r"(next_pos)
                   : "memory");
      /*
asm volatile (
      "str %x1, [%x0]\n\t"
      :
      : "r"(curr_addr), "r"(next_pos)
      : "memory"
      );
      */

      asm volatile("dsb sy" ::: "memory");
      *time_log += timer.elapsed();
      asm volatile("dc civac, %0" ::"r"(curr_addr) : "memory");
      asm volatile("dsb sy" ::: "memory");
      curr_pos = next_pos;
      scanned_size += block_size;
    }
  }
#pragma GCC pop_options
};

#endif // CXL_PERF_APP_DT_ACCESS_PATTERN_ARM_H

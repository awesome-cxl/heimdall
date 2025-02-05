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

#ifndef CXL_PERF_APP_DT_MMAP_ALLOC_H
#define CXL_PERF_APP_DT_MMAP_ALLOC_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define MAX_MEM_NODES (8 * sizeof(uint64_t))

class MmapAlloc {
public:
  MmapAlloc() = default;
  ~MmapAlloc() = default;
  void *alloc_mmap(size_t page_size, size_t size, int numa_id);
  void dealloc_mmap(void *addr, size_t size);
  size_t get_native_page_size();

private:
  int get_page_size_flags(size_t page_size);
  bool page_size_is_huge(size_t page_size);
  void bind_to_numa_node(void *addr, size_t size, int numa_id);
};

#endif // CXL_PERF_APP_DT_MMAP_ALLOC_H

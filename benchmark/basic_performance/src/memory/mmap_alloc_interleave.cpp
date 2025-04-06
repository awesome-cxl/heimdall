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
#include <memory/mmap_alloc_interleave.h>
#include <numa.h>
#include <numaif.h>
#include <stdexcept>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>

size_t MmapAllocInterleave::get_native_page_size() {
  long sz;

  sz = sysconf(_SC_PAGESIZE);
  if (sz < 0) {
    perror("failed to get native page size");
    exit(1);
  }

  return (size_t)sz;
}

bool MmapAllocInterleave::page_size_is_huge(size_t page_size) {
  return page_size > get_native_page_size();
}

static inline int mbind(void *addr, unsigned long len, int mode,
                        unsigned long *nodemask, unsigned long maxnode,
                        unsigned flags) {
  return syscall(__NR_mbind, addr, len, mode, nodemask, maxnode, flags);
}

int MmapAllocInterleave::get_page_size_flags(size_t page_size) {
  int lg = 0;

  if (!page_size || (page_size & (page_size - 1))) {
    fprintf(stderr, "page size must be a power of 2: %zu\n", page_size);
    exit(1);
  }

  if (!page_size_is_huge(page_size)) {
    return 0;
  }
  while (page_size >>= 1) {
    ++lg;
  }
  return MAP_HUGETLB | (lg << MAP_HUGE_SHIFT);
}

std::shared_ptr<struct MemAllocatedTable>
MmapAllocInterleave::get_allocated_table(void *addr, size_t size, int numa_nums,
                                         std::vector<uint32_t> &weighted_values,
                                         size_t page_mask) {
  auto allocated_table = std::make_shared<struct MemAllocatedTable>();
  allocated_table->total_size = size;
  allocated_table->mem_allocated_info.resize(numa_nums + 1);
  int numa_weight_sum = 0;
  for (int i = 0; i <= numa_nums; ++i) {
    numa_weight_sum += weighted_values[i];
  }
  size_t unit_size = static_cast<size_t>(size / numa_weight_sum) & ~page_mask;
  if (unit_size == 0) {
    throw std::runtime_error("Allocation size is too small");
  }
  if (unit_size < 1) {
    throw std::runtime_error("Allocation size is too small");
  }
  char *temp_addr = static_cast<char *>(addr);
  for (int i = 0; i < numa_nums + 1; ++i) {
    if (weighted_values[i] < 0) {
      throw std::runtime_error("NUMA node weight must be non-negative");
    }

    allocated_table->mem_allocated_info[i].addr =
        static_cast<void *>(temp_addr);
    allocated_table->mem_allocated_info[i].size =
        unit_size * weighted_values[i];
    allocated_table->mem_allocated_info[i].numa_id = i;
    temp_addr += i * unit_size * weighted_values[i];
  }

  return allocated_table;
}

void *MmapAllocInterleave::alloc_mmap(size_t page_size, size_t size,
                                      int numa_nums,
                                      std::vector<uint32_t> &weighted_values) {
  void *addr;
  size_t pagemask = page_size - 1;
  int flags = MAP_PRIVATE | MAP_ANONYMOUS | get_page_size_flags(page_size);
  if (numa_nums > CoreConfig::MAX_NUMA_NUM) {
    throw std::runtime_error("NUMA node count exceeds maximum limit");
  }

  size = (size + page_size) & ~pagemask;
  addr = mmap(0, size, PROT_READ | PROT_WRITE, flags, -1, 0);
  if (addr == MAP_FAILED) {
    perror("mmap");
    exit(1);
  }

  auto allocated_table =
      get_allocated_table(addr, size, numa_nums, weighted_values, pagemask);
  if (allocated_table == nullptr) {
    throw std::runtime_error("Failed to allocate memory");
  }
  for (int numa_idx = 0; numa_idx <= numa_nums; ++numa_idx) {
    if (weighted_values[numa_idx] < 0) {
      throw std::runtime_error("NUMA node weight must be non-negative");
    }
    if (numa_idx >= CoreConfig::MAX_NUMA_NUM) {
      throw std::runtime_error("NUMA node index exceeds maximum limit");
    }
    if (allocated_table->mem_allocated_info[numa_idx].size == 0) {
      continue;
    }
    bind_to_numa_node(allocated_table->mem_allocated_info[numa_idx].addr,
                      allocated_table->mem_allocated_info[numa_idx].size,
                      allocated_table->mem_allocated_info[numa_idx].numa_id);
  }

  if (!page_size_is_huge(page_size)) {
    if (madvise(addr, size, MADV_NOHUGEPAGE)) {
      perror("madvise");
    }
  }

  return addr;
}

void MmapAllocInterleave::dealloc_mmap(void *addr, size_t size) {
  if (munmap(addr, size)) {
    perror("munmap");
    exit(1);
  }
}

void MmapAllocInterleave::bind_to_numa_node(void *addr, size_t size,
                                            int numa_id) {
  if (numa_available() == -1) {
    throw std::runtime_error("NUMA is not available on this system");
  }

  unsigned long nodemask = (1UL << numa_id);
  int mode = MPOL_BIND;

  if (mbind(addr, size, mode, &nodemask, sizeof(nodemask) * 8, 0) != 0) {
    perror("Failed to bind memory to NUMA node");
    std::cout << "NUMA node: " << numa_id << std::endl;
    throw std::runtime_error("NUMA binding failed");
  }
  // std::cout << "Memory successfully bound to NUMA node: " << numa_id <<
  // std::endl;
}

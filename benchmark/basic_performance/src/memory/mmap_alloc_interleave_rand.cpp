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
#include <memory/mmap_alloc_interleave_rand.h>
#include <numa.h>
#include <numaif.h>
#include <stdexcept>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>

size_t MmapAllocInterleaveRand::get_native_page_size() {
  long sz;

  sz = sysconf(_SC_PAGESIZE);
  if (sz < 0) {
    perror("failed to get native page size");
    exit(1);
  }

  return (size_t)sz;
}

bool MmapAllocInterleaveRand::page_size_is_huge(size_t page_size) {
  return page_size > get_native_page_size();
}

static inline int mbind(void *addr, unsigned long len, int mode,
                        unsigned long *nodemask, unsigned long maxnode,
                        unsigned flags) {
  return syscall(__NR_mbind, addr, len, mode, nodemask, maxnode, flags);
}

int MmapAllocInterleaveRand::get_page_size_flags(size_t page_size) {
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

uint32_t MmapAllocInterleaveRand::get_weighted_numa_id(
    const std::vector<uint32_t> &weighted_values, int numa_nums) {
  uint32_t total_weight = 0;
  for (const auto &value : weighted_values) {
    total_weight += value;
  }

  uint32_t random_value = rand() % total_weight;
  uint32_t cumulative_weight = 0;

  for (int i = 0; i < numa_nums; ++i) {
    cumulative_weight += weighted_values[i];
    if (random_value < cumulative_weight) {
      return i;
    }
  }
  std::cerr << "Error: Random value exceeds total weight" << std::endl;
  return -1; // Should never reach here
}

void *
MmapAllocInterleaveRand::alloc_mmap(size_t page_size, size_t size,
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

  if (numa_available() == -1) {
    throw std::runtime_error("NUMA is not available on this system");
  }

  auto numa_id = get_weighted_numa_id(weighted_values, numa_nums);
  if (numa_id >= numa_nums) {
    std::cerr << "Error: NUMA ID exceeds available NUMA nodes" << std::endl;
    munmap(addr, size);
    return nullptr;
  }

  bind_to_numa_node(addr, size, numa_id);

  if (!page_size_is_huge(page_size)) {
    if (madvise(addr, size, MADV_NOHUGEPAGE)) {
      perror("madvise");
    }
  }

  return addr;
}

void MmapAllocInterleaveRand::dealloc_mmap(void *addr, size_t size) {
  if (munmap(addr, size)) {
    perror("munmap");
    exit(1);
  }
}

void MmapAllocInterleaveRand::bind_to_numa_node(void *addr, size_t size,
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

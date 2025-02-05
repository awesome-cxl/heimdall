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
#include <memory/mmap_alloc.h>
#include <numa.h>
#include <numaif.h>
#include <stdexcept>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>

size_t MmapAlloc::get_native_page_size() {
  long sz;

  sz = sysconf(_SC_PAGESIZE);
  if (sz < 0) {
    perror("failed to get native page size");
    exit(1);
  }

  return (size_t)sz;
}

bool MmapAlloc::page_size_is_huge(size_t page_size) {
  return page_size > get_native_page_size();
}

static inline int mbind(void *addr, unsigned long len, int mode,
                        unsigned long *nodemask, unsigned long maxnode,
                        unsigned flags) {
  return syscall(__NR_mbind, addr, len, mode, nodemask, maxnode, flags);
}

int MmapAlloc::get_page_size_flags(size_t page_size) {
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

void *MmapAlloc::alloc_mmap(size_t page_size, size_t size, int numa_id) {
  void *addr;
  size_t pagemask = page_size - 1;
  int flags = MAP_PRIVATE | MAP_ANONYMOUS | get_page_size_flags(page_size);

  size = (size + pagemask) & ~pagemask;
  addr = mmap(0, size, PROT_READ | PROT_WRITE, flags, -1, 0);
  if (addr == MAP_FAILED) {
    perror("mmap");
    exit(1);
  }

  bind_to_numa_node(addr, size, numa_id);

  if (!page_size_is_huge(page_size)) {
    if (madvise(addr, size, MADV_NOHUGEPAGE)) {
      perror("madvise");
    }
  }

  return addr;
}

void MmapAlloc::dealloc_mmap(void *addr, size_t size) {
  if (munmap(addr, size)) {
    perror("munmap");
    exit(1);
  }
}

void MmapAlloc::bind_to_numa_node(void *addr, size_t size, int numa_id) {
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

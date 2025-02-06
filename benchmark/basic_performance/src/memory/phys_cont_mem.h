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

#pragma once

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <sys/mman.h>
#include <unistd.h>
#include <unordered_map>
#include <vector>

#ifndef PAGEMAP_LENGTH
#define PAGEMAP_LENGTH 8
#endif

class PhysContMem {
public:
  PhysContMem() : page_size(getpagesize()) {
    if (page_size == -1UL) {
      throw std::runtime_error("Failed to get page size. getpagesize: " +
                               std::string(strerror(errno)));
    } else {
      std::cerr << "Page size: " << page_size << " bytes.\n";
    }
  }

  bool verbose = false;

  // Number of additional pages to allocate at for each page requested
  // Extra pages are released after the call to alloc()
  size_t allocation_amplification_factor = 10;

  // Maximum number of allocation retries
  size_t max_allocation_retries = 10;

  // Main function to allocate and remap memory
  // Returns non-null pointer to a physically contiguous memory region, or
  // nullptr on failure Sets errorno on failure
  void *alloc(size_t bytes, void *hint = (void *)0x100000000) {
    for (size_t i = 0; i < max_allocation_retries; i++) {
      void *result = _alloc(bytes, hint);
      if (result != nullptr) {
        allocation_map[result] = bytes;
        return result;
      }
    }

    return nullptr;
  }

  void dealloc(void *ptr) {
    if (allocation_map.find(ptr) != allocation_map.end()) {
      munmap(ptr, allocation_map[ptr]);
      allocation_map.erase(ptr);
    }
  }

  // Function to check if a memory region is contiguous in physical address
  // space
  bool is_physically_contiguous(void *start_addr, size_t size) {
    const size_t numPages =
        (size + page_size - 1) / page_size; // Round up to cover partial pages

    std::vector<size_t> pfns(numPages);

    // Get the PFN for each page in the region
    for (size_t i = 0; i < numPages; i++) {
      void *pageAddr = (unsigned char *)start_addr + (i * page_size);
      const size_t pfn = get_pfn_of_addr(pageAddr);
      if (pfn == 0) {
        if (verbose)
          std::cerr << "Failed to get PFN for address " << pageAddr << "\n";

        return false;
      }
      pfns[i] = pfn;
    }

    // Check if the PFNs are consecutive
    for (size_t i = 1; i < numPages; i++) {
      if (pfns[i] != pfns[i - 1] + 1) {
        return false; // Not contiguous
      }
    }

    return true; // All PFNs are consecutive
  }

private:
  size_t page_size = -1UL;
  std::unordered_map<void *, size_t> allocation_map;

  template <typename T> size_t get_pfn_of_addr(T addr_raw) {
    const auto addr = (void *)addr_raw;
    FILE *pagemap = fopen("/proc/self/pagemap", "rb");
    if (!pagemap) {
      throw std::runtime_error("Failed to open /proc/self/pagemap. fopen: " +
                               std::string(strerror(errno)));
    }

    const size_t offset = (size_t)addr / page_size * PAGEMAP_LENGTH;
    if (fseek(pagemap, (long)offset, SEEK_SET) != 0) {
      throw std::runtime_error(
          "Failed to seek pagemap to proper location. fseek: " +
          std::string(strerror(errno)));
    }

    size_t page_frame_number = 0;
    // Read 7 bytes (lower 55 bits hold the PFN)
    const auto bytes_read =
        fread(&page_frame_number, 1, PAGEMAP_LENGTH - 1, pagemap);

    if (bytes_read != PAGEMAP_LENGTH - 1) {
      throw std::runtime_error("Failed to read pagemap. fread: " +
                               std::string(strerror(errno)));
    }

    page_frame_number &= 0x7FFFFFFFFFFFFF;

    fclose(pagemap);
    return page_frame_number;
  }

  void *_alloc(size_t bytes, void *hint) {
    int N = bytes / page_size;
    if (N <= 0) {
      return nullptr; // Invalid size
    }

    // We will allocate allocation_amplification_factor * N pages
    const int totalPages = allocation_amplification_factor * N;
    size_t allocSize = (size_t)totalPages * page_size;

    // Create one large allocation
    void *base = mmap(nullptr, allocSize, PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (base == MAP_FAILED) {
      return nullptr; // Allocation failed
    }

    // Store (PFN, VA) for each allocated page
    std::vector<std::pair<size_t, void *>> pfnVaPairs(totalPages);

    // Touch each page to ensure it is backed by real memory, then find its PFN
    for (int i = 0; i < totalPages; i++) {
      void *addr = (unsigned char *)base + (i * page_size);
      // Force a real mapping
      *(volatile char *)addr = 0;

      size_t pfn = get_pfn_of_addr(addr);
      pfnVaPairs[i] = std::make_pair(pfn, addr);
    }

    // Sort pages by their PFN
    std::sort(pfnVaPairs.begin(), pfnVaPairs.end(),
              [](auto &a, auto &b) { return a.first < b.first; });

    // Find the largest run of consecutive PFNs
    int bestLen = 1;
    int bestStart = 0;

    int currentLen = 1;
    int currentStart = 0;

    for (int i = 1; i < totalPages; i++) {
      if (pfnVaPairs[i].first == pfnVaPairs[i - 1].first + 1) {
        currentLen++;
      } else {
        if (currentLen > bestLen) {
          bestLen = currentLen;
          bestStart = currentStart;
        }
        currentLen = 1;
        currentStart = i;
      }
    }
    // Check at the end
    if (currentLen > bestLen) {
      bestLen = currentLen;
      bestStart = currentStart;
    }

    if (verbose)
      std::cerr << "Largest consecutive PFN run: " << bestLen << " pages.\n";

    if (bestLen < N) {
      if (verbose)
        std::cerr << "Could not find " << N << " consecutive physical pages.\n";
      // Clean up
      munmap(base, allocSize);
      return nullptr;
    }

    if (verbose)
      std::cerr << "Success: Found at least " << N
                << " consecutive physical pages.\n";

    // Reserve a new region at 0x100000000 for these N pages
    // This region must be unmapped before calling MAP_FIXED, or we can do
    // an anonymous mmap to reserve that space.
    void *newBase = hint;
    size_t newSize = (size_t)N * page_size;

    // Map the new address range (just to reserve it)
    void *fixedMapping = mmap(newBase, newSize, PROT_READ | PROT_WRITE,
                              MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED, -1, 0);
    if (fixedMapping == MAP_FAILED) {
      if (verbose)
        std::cerr << "Failed to mmap the new region at 0x100000000.\n";
      munmap(base, allocSize);
      errno = ENOMEM;
      return nullptr;
    }

    if (verbose)
      std::cerr << "Remapping pages to " << hint << "...\n";

    // Move each page in the found run to the new region
    // We'll do it one page at a time.
    for (int i = bestStart; i < bestStart + N; i++) {
      void *oldAddr = pfnVaPairs[i].second;
      void *newAddr =
          (void *)((unsigned char *)newBase + (i - bestStart) * page_size);

      // Perform the remap
      void *result = mremap(oldAddr, page_size, page_size,
                            MREMAP_MAYMOVE | MREMAP_FIXED, newAddr);
      const auto mremap_errno = errno;
      if (result == MAP_FAILED) {
        if (verbose)
          std::cerr << "mremap failed at index " << i << "\n";

        // Clean up
        munmap(fixedMapping, newSize);
        munmap(base, allocSize);

        errno = mremap_errno;

        return nullptr;
      }
    }

    // Unmap any leftover pages in the original allocation
    // The pages we moved should no longer reside there, but let's clean up
    // whatever remains in that original area.
    munmap(base, allocSize);

    if (verbose)
      std::cerr << "Remap completed. The pages are now virtually contiguous at "
                   "0x100000000.\n";

    // At this point, the memory for the N pages is at 0x100000000 to
    // 0x100000000 + (N*page_size - 1)

    if (verbose) {
      std::cerr << "Is the new region physically contiguous? " << std::boolalpha
                << is_physically_contiguous(newBase, newSize) << "\n";
      std::cerr << "Region size: " << newSize / 1024 / 1024 << " MiB.\n";
    }

    // Normally, you might do some work here, then eventually unmap:
    // munmap(newBase, newSize);

    return is_physically_contiguous(newBase, newSize) ? newBase : nullptr;
  }
};

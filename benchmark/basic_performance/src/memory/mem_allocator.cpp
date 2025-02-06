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
#include <memory/huge_page_handler.h>
#include <memory/mem_allocator.h>
#include <memory/mmap_alloc.h>
#include <memory/phys_cont_mem.h>
#include <sys/mman.h>

PhysContMem *memory_manager = nullptr;
MmapAlloc *mmap_manager = nullptr;

void *MemAllocator::allocate(size_t size, int numa_id,
                             MemAllocType alloc_type) {
  if (alloc_type == MemAllocType::NON_CONTIGUOUS_HUGE_PAGE) {
    if (mmap_manager == nullptr) {
      mmap_manager = new MmapAlloc();
    }
    return mmap_manager->alloc_mmap(mmap_manager->get_native_page_size(), size,
                                    numa_id);
  } else if (alloc_type == MemAllocType::CONTIGUOUS_HUGE_PAGE) {
    if (!memory_manager) {
      memory_manager = new PhysContMem();
    }

    size_t amplification = 10;

    if (size < 1024 * 1024 * 1024UL) {
      amplification = 56; // Try to allocate upto 56 GiB
    } else if (size <= 4 * 1024 * 1024 * 1024UL) {
      amplification = 20; // Try to allocate upto 80-ish GiB
    } else {
      amplification = 10;
    }

    memory_manager->verbose = true;
    memory_manager->max_allocation_retries = 10;
    memory_manager->allocation_amplification_factor = amplification;

    return memory_manager->alloc(size);
  } else {
    std::cerr << "Invalid allocation type" << std::endl;
    return nullptr;
  }
}

void MemAllocator::deallocate(void *ptr, size_t size, MemAllocType alloc_type) {
  if (alloc_type == MemAllocType::NON_CONTIGUOUS_HUGE_PAGE) {
    if (mmap_manager == nullptr) {
      mmap_manager = new MmapAlloc();
    }
    mmap_manager->dealloc_mmap(ptr, size);
  } else if (alloc_type == MemAllocType::CONTIGUOUS_HUGE_PAGE) {
    if (!memory_manager) {
      memory_manager = new PhysContMem();
    }
    memory_manager->dealloc(ptr);
  } else {
    std::cerr << "Invalid allocation type" << std::endl;
  }
}

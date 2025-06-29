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

#ifndef CXL_PERF_APP_DT_HUGE_PAGE_HANDLER_H
#define CXL_PERF_APP_DT_HUGE_PAGE_HANDLER_H
#include <core/system_define.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

class HugePageHandler {
public:
  static void *allocate_huge_page(size_t size, int numa_id);
  static void deallocate_huge_page(void *addr, size_t size);

private:
  static void setup_numa_hugepages(size_t num_pages, int numa_node);
  static void mount_hugetlbfs(const std::string &mount_path);
  static size_t get_hugepage_size();
  static void bind_to_numa_node(void *addr, size_t size, int numa_id);
  static bool directory_exists(const std::string &path);
  static void cleanup_hugepage_resources();
};

#endif // CXL_PERF_APP_DT_HUGE_PAGE_HANDLER_H

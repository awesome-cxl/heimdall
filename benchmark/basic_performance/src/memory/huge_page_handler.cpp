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

#include <cmath>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <memory/huge_page_handler.h>
#include <numa.h>
#include <numaif.h>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <unistd.h>

size_t HugePageHandler::get_hugepage_size() {
  std::ifstream meminfo("/proc/meminfo");
  std::string line;

  while (std::getline(meminfo, line)) {
    if (line.find("Hugepagesize") != std::string::npos) {
      size_t size_kb;
      sscanf(line.c_str(), "Hugepagesize: %zu kB", &size_kb);
      return size_kb * 1024; // KiB to Bytes
    }
  }
  throw std::runtime_error(
      "Failed to determine HugePage size from /proc/meminfo");
}

void HugePageHandler::setup_numa_hugepages(size_t num_pages, int numa_node) {
  std::string numa_hugepages_path = "/sys/devices/system/node/node" +
                                    std::to_string(numa_node) +
                                    "/hugepages/hugepages-2048kB/nr_hugepages";
  std::ofstream numa_hugepages_file(numa_hugepages_path);
  if (!numa_hugepages_file.is_open()) {
    throw std::runtime_error("Failed to open NUMA hugepages file for node: " +
                             std::to_string(numa_node));
  }
  numa_hugepages_file << num_pages;
  std::cout << "Set " << num_pages << " HugePages for NUMA node " << numa_node
            << "." << std::endl;
}

bool HugePageHandler::directory_exists(const std::string &path) {
  struct stat info;
  return (stat(path.c_str(), &info) == 0 && S_ISDIR(info.st_mode));
}

void HugePageHandler::mount_hugetlbfs(const std::string &mount_path) {
  if (directory_exists(mount_path)) {
    std::cout << "Directory already exists: " << mount_path << std::endl;
  } else {
    if (mkdir(mount_path.c_str(), 0755) != 0) {
      perror("Failed to create mount directory");
      throw std::runtime_error("Failed to create mount directory: " +
                               mount_path);
    }
    std::cout << "Created mount directory: " << mount_path << std::endl;
  }

  if (mount("none", mount_path.c_str(), "hugetlbfs", 0, nullptr) != 0) {
    perror("Failed to mount hugetlbfs");
    throw std::runtime_error("Failed to mount hugetlbfs at: " + mount_path);
  }

  std::cout << "Mounted hugetlbfs at: " << mount_path << std::endl;
}

void HugePageHandler::bind_to_numa_node(void *addr, size_t size, int numa_id) {
  if (numa_available() == -1) {
    throw std::runtime_error("NUMA is not available on this system");
  }

  unsigned long nodemask = (1UL << numa_id);
  int mode = MPOL_BIND;

  if (mbind(addr, size, mode, &nodemask, sizeof(nodemask) * 8, 0) != 0) {
    perror("Failed to bind memory to NUMA node");
    throw std::runtime_error("NUMA binding failed");
  }

  std::cout << "Memory successfully bound to NUMA node: " << numa_id
            << std::endl;
}

void *HugePageHandler::allocate_huge_page(size_t size, int numa_node) {
  const char *mount_path = "/mnt/huge";
  size_t hugepage_size = get_hugepage_size();

  size_t num_pages = std::ceil(static_cast<double>(size) / hugepage_size);
  std::cout << "Calculated HugePages needed: " << num_pages << " pages"
            << std::endl;

  setup_numa_hugepages(num_pages, numa_node);
  mount_hugetlbfs(mount_path);

  const char *template_path = "/mnt/huge/hugepagefileXXXXXX";
  char unique_path[256];
  strcpy(unique_path, template_path);

  int fd = mkstemp(unique_path);
  if (fd < 0) {
    perror("Failed to create temporary hugepage file");
    return nullptr;
  }

  if (ftruncate(fd, size) < 0) {
    perror("Failed to set file size");
    close(fd);
    return nullptr;
  }

  void *addr = mmap(nullptr, size, PROT_READ | PROT_WRITE,
                    MAP_SHARED | MAP_HUGETLB, fd, 0);
  if (addr == MAP_FAILED) {
    perror("Failed to map hugepages");
    std::cerr << "Requested size: " << size << " bytes" << std::endl;
    std::cerr << "HugePage size: " << hugepage_size << " bytes" << std::endl;
    std::cerr << "Requested pages: " << num_pages << std::endl;
    return nullptr;
  }

  bind_to_numa_node(addr, size, numa_node);

  std::cout << "HugePages allocated at address: " << addr << ", size: " << size
            << " bytes" << std::endl;

  close(fd);
  unlink(unique_path);

  return addr;
}

void HugePageHandler::deallocate_huge_page(void *addr, size_t size) {
  if (munmap(addr, size) < 0) {
    perror("Failed to unmap hugepages");
  } else {
    std::cout << "HugePages unmapped from address: " << addr
              << ", size: " << size << " bytes" << std::endl;
  }
  cleanup_hugepage_resources();
}

void HugePageHandler::cleanup_hugepage_resources() {
  std::string mount_path = "/mnt/huge";
  struct stat info;
  if (stat(mount_path.c_str(), &info) == 0 && S_ISDIR(info.st_mode)) {
    if (umount(mount_path.c_str()) == 0) {
      std::cout << "Successfully unmounted hugetlbfs from: " << mount_path
                << std::endl;
      if (rmdir(mount_path.c_str()) == 0) {
        std::cout << "Removed directory: " << mount_path << std::endl;
      } else {
        perror("Failed to remove directory");
      }
    } else {
      perror("Failed to unmount hugetlbfs");
    }
  }
}

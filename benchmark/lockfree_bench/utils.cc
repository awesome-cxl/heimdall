#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <numa.h>
#include <numaif.h>

#include <iostream>

#include "utils.hh"

void set_thread_affinity(pthread_t thread, int core_id) {
  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  CPU_SET(core_id, &cpuset);

  int rc = pthread_setaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
  if (rc != 0) {
    char error_msg[256];
    strerror_r(rc, error_msg, sizeof(error_msg));
    std::cerr << "CPU affinity failed: " << error_msg << "\n";
  }
}

void bind_numa_node(int node) {
  auto mask = numa_allocate_nodemask();
  numa_bitmask_clearall(mask);
  numa_bitmask_setbit(mask, node);
  numa_set_membind(mask);
}

#ifndef CXLBENCH_UTILS_H
#define CXLBENCH_UTILS_H

#include <pthread.h>

void set_thread_affinity(pthread_t thread, int core_id);
void bind_numa_node(int node);

#endif

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <numa.h>
#include <numaif.h>

#include <chrono>
#include <iostream>
#include <random>
#include <thread>

#include "BoostSPSCQueueBench.hh"
#include "utils.hh"

typedef boost::lockfree::spsc_queue<uint64_t> q_t;

CXLBench<q_t>::CXLBench(size_t size, int qNumaNode, int setterNumaNode,
                        int getterNumaNode, int setterCore, int getterCore)
    : size(size), qNumaNode(qNumaNode), setterNumaNode(setterNumaNode),
      getterNumaNode(getterNumaNode), setterCore(setterCore),
      getterCore(getterCore) {}

void CXLBench<q_t>::init() {
  // elem: q_t::value_type == uint64_t
  qElemsNum = size / sizeof(uint64_t);
  std::cout << "Size of queue: " << size << std::endl;
  std::cout << "Number of elements in queue: " << qElemsNum << std::endl;

  q = static_cast<q_t *>(numa_alloc_onnode(sizeof(q_t), qNumaNode));
  new (q) q_t(qElemsNum);
}

void CXLBench<q_t>::run(size_t rounds) {
  decltype(std::chrono::steady_clock::now()) setterStart;
  decltype(std::chrono::steady_clock::now()) getterStart;
  decltype(std::chrono::steady_clock::now()) setterEnd;
  decltype(std::chrono::steady_clock::now()) getterEnd;

  std::thread set_thread([this, rounds, &setterStart, &setterEnd]() {
    set_thread_affinity(pthread_self(), this->setterCore);
    bind_numa_node(this->qNumaNode);

    setterStart = std::chrono::steady_clock::now();

    for (size_t i = 0; i < rounds; ++i) {
      while (true) {
        if (q->push((uint64_t)i))
          break;
      }
    }

    setterEnd = std::chrono::steady_clock::now();
  });

  std::thread get_thread([this, rounds, &getterStart, &getterEnd]() {
    set_thread_affinity(pthread_self(), this->getterCore);
    // bind_numa_node(this->mapNumaNode);

    uint64_t val;

    getterStart = std::chrono::steady_clock::now();

    for (size_t i = 0; i < rounds; ++i) {
      while (true) {
        if (q->pop(val))
          break;
      }
    }

    getterEnd = std::chrono::steady_clock::now();
  });

  set_thread.join();
  get_thread.join();

  auto start = std::min(setterStart, getterStart);
  auto end   = std::max(setterEnd, getterEnd);

  std::cout << std::chrono::duration_cast<std::chrono::nanoseconds>(end - start)
                   .count()
            << " ns" << std::endl;
}

void CXLBench<q_t>::clean() {
  q->reset();
  numa_free(q, sizeof(q_t));
  q = nullptr;
}

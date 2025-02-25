#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <numa.h>
#include <numaif.h>

#include <chrono>
#include <iostream>
#include <random>
#include <thread>

#include "FollyAtomicHashMapBench.hh"
#include "utils.hh"

typedef folly::AtomicHashMap<uint64_t, uint64_t> map_t;

CXLBench<map_t>::CXLBench(size_t size, int mapNumaNode, int setterNumaNode,
                          int getterNumaNode, int setterCore, int getterCore)
    : size(size), mapNumaNode(mapNumaNode), setterNumaNode(setterNumaNode),
      getterNumaNode(getterNumaNode), setterCore(setterCore),
      getterCore(getterCore), setterSeq(nullptr), getterSeq(nullptr) {}

void CXLBench<map_t>::init() {
  // key: uint64_t, val: uint64_t
  mapEntriesNum = size / (sizeof(uint64_t) * 2);
  std::cout << "Size of map: " << size << std::endl;
  std::cout << "Number of entries in map: " << mapEntriesNum << std::endl;

  m = static_cast<map_t *>(numa_alloc_onnode(sizeof(map_t), mapNumaNode));
  new (m) map_t(mapEntriesNum);

  for (size_t i = 0; i < mapEntriesNum; ++i) {
    while (true) {
      auto res = m->insert((uint64_t)i, (uint64_t)i);
      if (res.second) {
        break;
      }
    }
  }
}

void CXLBench<map_t>::run(size_t rounds) {
  setterSeq = static_cast<uint64_t *>(
      numa_alloc_onnode(rounds * sizeof(uint64_t), setterNumaNode));
  getterSeq = static_cast<uint64_t *>(
      numa_alloc_onnode(rounds * sizeof(uint64_t), getterNumaNode));

  std::random_device rd;
  std::mt19937 gen(rd());
  std::uniform_int_distribution<uint64_t> distrib(0, mapEntriesNum);

  for (size_t i = 0; i < rounds; ++i) {
    setterSeq[i] = distrib(gen);
    getterSeq[i] = distrib(gen);
  }

  decltype(std::chrono::steady_clock::now()) setterStart;
  decltype(std::chrono::steady_clock::now()) getterStart;
  decltype(std::chrono::steady_clock::now()) setterEnd;
  decltype(std::chrono::steady_clock::now()) getterEnd;

  std::thread set_thread([this, rounds, &setterStart, &setterEnd]() {
    set_thread_affinity(pthread_self(), this->setterCore);
    bind_numa_node(this->mapNumaNode);

    setterStart = std::chrono::steady_clock::now();

    for (size_t i = 0; i < rounds; ++i) {
      auto ret = m->insert(this->setterSeq[i], this->setterSeq[i]);
      if (!ret.second) { // key already exists, increment val by 1
        ret.first->second += 1;
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
      auto ret = m->find(this->getterSeq[i]);
      if (ret != m->end()) {
        val = ret->second;
      }
    }

    getterEnd = std::chrono::steady_clock::now();
  });

  set_thread.join();
  get_thread.join();

  numa_free(setterSeq, rounds * sizeof(uint64_t));
  numa_free(getterSeq, rounds * sizeof(uint64_t));
  setterSeq = nullptr;
  getterSeq = nullptr;

  auto start = std::min(setterStart, getterStart);
  auto end   = std::max(setterEnd, getterEnd);

  std::cout << std::chrono::duration_cast<std::chrono::nanoseconds>(end - start)
                   .count()
            << " ns" << std::endl;
}

void CXLBench<map_t>::clean() {
  m->~AtomicHashMap();
  numa_free(m, sizeof(map_t));
  m = nullptr;
}

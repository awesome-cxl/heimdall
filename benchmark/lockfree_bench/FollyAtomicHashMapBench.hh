#ifndef CXLBENCH_FOLLY_ATOMICHASHMAP_H
#define CXLBENCH_FOLLY_ATOMICHASHMAP_H

#include "CXLBench.hh"

#include <folly/AtomicHashMap.h>

template <> class CXLBench<folly::AtomicHashMap<uint64_t, uint64_t>> {
private:
  folly::AtomicHashMap<uint64_t, uint64_t> *m;
  size_t size;
  size_t mapEntriesNum;
  int mapNumaNode;
  int setterNumaNode;
  int getterNumaNode;
  int setterCore;
  int getterCore;
  uint64_t *setterSeq;
  uint64_t *getterSeq;

public:
  CXLBench(size_t size, int mapNumaNode, int setterNumaNode, int getterNumaNode,
           int setterCore, int getterCore);
  void init();
  void run(size_t rounds);
  void clean();
};

#endif

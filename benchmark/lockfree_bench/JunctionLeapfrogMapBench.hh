#ifndef CXLBENCH_JUNCTION_LEAPFROGMAP_H
#define CXLBENCH_JUNCTION_LEAPFROGMAP_H

#include "CXLBench.hh"

#include <junction/ConcurrentMap_Leapfrog.h>
#include <junction/Core.h>
#include <junction/QSBR.h>
#include <turf/Util.h>

template <>
class CXLBench<junction::ConcurrentMap_Leapfrog<uint64_t, uint64_t>> {
private:
  junction::ConcurrentMap_Leapfrog<uint64_t, uint64_t> *m;
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
  void init(junction::QSBR::Context &context);
  void run(size_t rounds);
  void clean();
};

#endif

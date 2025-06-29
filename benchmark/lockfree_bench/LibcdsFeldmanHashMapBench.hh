#ifndef CXLBENCH_LIBCDS_FELDMANHASHMAP_H
#define CXLBENCH_LIBCDS_FELDMANHASHMAP_H

#include "CXLBench.hh"

#include <cds/container/feldman_hashmap_hp.h>
#include <cds/gc/hp.h> // for cds::HP (Hazard Pointer) SMR
#include <cds/init.h>  // for cds::Initialize and cds::Terminate

template <>
class CXLBench<
    cds::container::FeldmanHashMap<cds::gc::HP, uint64_t, uint64_t>> {
private:
  cds::container::FeldmanHashMap<cds::gc::HP, uint64_t, uint64_t> *m;
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

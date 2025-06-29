#ifndef CXLBENCH_LIBCDS_BRONSONAVLTREEMAP_H
#define CXLBENCH_LIBCDS_BRONSONAVLTREEMAP_H

#include "CXLBench.hh"

#include <cds/urcu/general_buffered.h>

#include <cds/container/bronson_avltree_map_rcu.h>

template <>
class CXLBench<cds::container::BronsonAVLTreeMap<
    cds::urcu::gc<cds::urcu::general_buffered<>>, uint64_t, uint64_t>> {
private:
  cds::container::BronsonAVLTreeMap<
      cds::urcu::gc<cds::urcu::general_buffered<>>, uint64_t, uint64_t> *m;
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

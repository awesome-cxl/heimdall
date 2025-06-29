#ifndef CXLBENCH_LIBCDS_MICHAELHASHMAP_H
#define CXLBENCH_LIBCDS_MICHAELHASHMAP_H

#include "CXLBench.hh"

#include <cds/container/michael_kvlist_hp.h> // MichaelKVList for gc::HP
#include <cds/container/michael_map.h>       // MichaelHashMap
#include <cds/gc/hp.h>                       // for cds::HP (Hazard Pointer) SMR
#include <cds/init.h> // for cds::Initialize and cds::Terminate

// List traits based on std::less predicate
struct MichaelListTraits : public cds::container::michael_list::traits {
  typedef std::less<uint64_t> less;
};

// Ordered list
typedef cds::container::MichaelKVList<cds::gc::HP, uint64_t, uint64_t,
                                      MichaelListTraits>
    MichaelListT;

// Map traits
struct MichaelMapTraits : public cds::container::michael_map::traits {
  struct hash {
    size_t operator()(uint64_t i) const {
      return cds::opt::v::hash<uint64_t>()(i);
    }
  };
};

template <>
class CXLBench<cds::container::MichaelHashMap<cds::gc::HP, MichaelListT,
                                              MichaelMapTraits>> {
private:
  cds::container::MichaelHashMap<cds::gc::HP, MichaelListT, MichaelMapTraits>
      *m;
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

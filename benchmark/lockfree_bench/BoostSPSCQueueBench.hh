#ifndef CXLBENCH_BOOST_SPSCQUEUE_H
#define CXLBENCH_BOOST_SPSCQUEUE_H

#include "CXLBench.hh"

#include <boost/lockfree/spsc_queue.hpp>

template <> class CXLBench<boost::lockfree::spsc_queue<uint64_t>> {
private:
  boost::lockfree::spsc_queue<uint64_t> *q;
  size_t size;
  size_t qElemsNum;
  int qNumaNode;
  int setterNumaNode;
  int getterNumaNode;
  int setterCore;
  int getterCore;

public:
  CXLBench(size_t size, int qNumaNode, int setterNumaNode, int getterNumaNode,
           int setterCore, int getterCore);
  void init();
  void run(size_t rounds);
  void clean();
};

#endif

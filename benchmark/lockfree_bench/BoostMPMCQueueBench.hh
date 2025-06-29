#ifndef CXLBENCH_BOOST_MPMCQUEUE_H
#define CXLBENCH_BOOST_MPMCQUEUE_H

#include "CXLBench.hh"

#include <boost/lockfree/queue.hpp>

template <> class CXLBench<boost::lockfree::queue<uint64_t>> {
private:
  boost::lockfree::queue<uint64_t> *q;
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

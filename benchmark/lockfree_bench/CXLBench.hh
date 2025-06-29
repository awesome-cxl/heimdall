#ifndef CXLBENCH_CXLBENCH_H
#define CXLBENCH_CXLBENCH_H

template <typename T> class CXLBench {
  virtual ~CXLBench() = 0;

  virtual void init()             = 0;
  virtual void run(size_t rounds) = 0;
  virtual void clean()            = 0;
};

#endif

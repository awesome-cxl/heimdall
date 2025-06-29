#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <sys/prctl.h>

#include <iostream>

#include <cxxopts.hpp>

#include "utils.hh"

#include "BoostMPMCQueueBench.hh"
#include "BoostSPSCQueueBench.hh"
#include "FollyAtomicHashMapBench.hh"
#include "JunctionGrampaMapBench.hh"
#include "JunctionLeapfrogMapBench.hh"
#include "JunctionLinearMapBench.hh"
#include "LibcdsBronsonAVLTreeMapBench.hh"
#include "LibcdsFeldmanHashMapBench.hh"
#include "LibcdsMichaelHashMapBench.hh"
#include "LibcdsSkipListMapBench.hh"
// #include "TervelWFHashMapBench.hh"

int main(int argc, char *argv[]) {
  cxxopts::Options options("CXLBench", "");

  options.add_options()("list", "List all supported data structures",
                        cxxopts::value<bool>()->default_value("false"));
  options.add_options()(
      "ds_type", "Data structure type",
      cxxopts::value<std::string>()->default_value("boost_spsc_queue"));
  options.add_options()("ds_size_mb", "Data structure's size in MB",
                        cxxopts::value<size_t>()->default_value("8"));
  options.add_options()("loop_rounds", "Loop rounds of operations",
                        cxxopts::value<size_t>()->default_value("1000000"));
  options.add_options()("setter_core", "Setter thread CPU core binding",
                        cxxopts::value<int>()->default_value("0"));
  options.add_options()("getter_core", "Getter thread CPU core binding",
                        cxxopts::value<int>()->default_value("1"));
  options.add_options()("setter_numa_node", "Setter thread numa node binding",
                        cxxopts::value<int>()->default_value("0"));
  options.add_options()("getter_numa_node", "Getter thread numa node binding",
                        cxxopts::value<int>()->default_value("0"));
  options.add_options()("ds_numa_node", "Data structure placement numa node",
                        cxxopts::value<int>()->default_value("0"));

  auto opts_result = options.parse(argc, argv);
  if (opts_result["list"].as<bool>()) {
    return 0;
  }

  std::string dsType = opts_result["ds_type"].as<std::string>();
  size_t dsSizeMB    = opts_result["ds_size_mb"].as<size_t>();
  size_t dsSize      = dsSizeMB << 20;
  size_t loopRounds  = opts_result["loop_rounds"].as<size_t>();

  int setterCore     = opts_result["setter_core"].as<int>();
  int getterCore     = opts_result["getter_core"].as<int>();
  int setterNumaNode = opts_result["setter_numa_node"].as<int>();
  int getterNumaNode = opts_result["getter_numa_node"].as<int>();
  int dsNumaNode     = opts_result["ds_numa_node"].as<int>();

  // disable transparent huge page table
  if (prctl(PR_SET_THP_DISABLE, 1, 0, 0, 0) == -1) {
    std::cerr << "prctl(PR_SET_THP_DISABLE) failed" << std::endl;
    return 1;
  }

  // bind the main thread to the numa node of the data structure
  bind_numa_node(dsNumaNode);

  if (dsType == "boost_spsc_queue") {
    typedef boost::lockfree::spsc_queue<uint64_t> q_t;
    CXLBench<q_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                        setterCore, getterCore);
    bench.init();
    bench.run(loopRounds);
    bench.clean();
  } else if (dsType == "boost_mpmc_queue") {
    typedef boost::lockfree::queue<uint64_t> q_t;
    CXLBench<q_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                        setterCore, getterCore);
    bench.init();
    bench.run(loopRounds);
    bench.clean();
  } else if (dsType == "folly_atomichashmap_map") {
    typedef folly::AtomicHashMap<uint64_t, uint64_t> map_t;
    CXLBench<map_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                          setterCore, getterCore);
    bench.init();
    bench.run(loopRounds);
    bench.clean();
  } else if (dsType == "libcds_michaelhashmap_map") {
    // Initialize libcds
    cds::Initialize();
    {
      cds::gc::HP hpGC;
      cds::threading::Manager::attachThread();

      typedef cds::container::MichaelHashMap<cds::gc::HP, MichaelListT,
                                             MichaelMapTraits>
          map_t;
      CXLBench<map_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                            setterCore, getterCore);
      bench.init();
      bench.run(loopRounds);
      bench.clean();

      // Detach thread when terminating
      cds::threading::Manager::detachThread();
    }
    // Terminate libcds
    cds::Terminate();
  } else if (dsType == "libcds_feldmanhashmap_map") {
    // Initialize libcds
    cds::Initialize();
    {
      cds::gc::HP hpGC;
      cds::threading::Manager::attachThread();

      typedef cds::container::FeldmanHashMap<cds::gc::HP, uint64_t, uint64_t>
          map_t;
      CXLBench<map_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                            setterCore, getterCore);
      bench.init();
      bench.run(loopRounds);
      bench.clean();

      // Detach thread when terminating
      cds::threading::Manager::detachThread();
    }
    // Terminate libcds
    cds::Terminate();
  } else if (dsType == "libcds_skiplistmap_map") {
    // Initialize libcds
    cds::Initialize();
    {
      cds::gc::HP myhp(67);
      cds::threading::Manager::attachThread();

      typedef cds::container::SkipListMap<cds::gc::HP, uint64_t, uint64_t>
          map_t;
      CXLBench<map_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                            setterCore, getterCore);
      bench.init();
      bench.run(loopRounds);
      bench.clean();

      // Detach thread when terminating
      cds::threading::Manager::detachThread();
    }
    // Terminate libcds
    cds::Terminate();
  } else if (dsType == "libcds_bronsonavltreemap_map") {
    // Initialize libcds
    cds::Initialize();
    {
      // Initialize general_buffered RCU
      cds::urcu::gc<cds::urcu::general_buffered<>> gpbRCU;
      cds::threading::Manager::attachThread();

      typedef cds::container::BronsonAVLTreeMap<
          cds::urcu::gc<cds::urcu::general_buffered<>>, uint64_t, uint64_t>
          map_t;
      CXLBench<map_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                            setterCore, getterCore);
      bench.init();
      bench.run(loopRounds);
      bench.clean();

      // Detach thread when terminating
      cds::threading::Manager::detachThread();
    }
    // Terminate libcds
    cds::Terminate();
  } else if (dsType == "junction_linearmap_map") {
    junction::QSBR::Context context = junction::DefaultQSBR.createContext();

    typedef junction::ConcurrentMap_Linear<uint64_t, uint64_t> map_t;
    CXLBench<map_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                          setterCore, getterCore);
    bench.init(context);
    bench.run(loopRounds);
    bench.clean();

    junction::DefaultQSBR.destroyContext(context);
    // } else if (dsType == "tervel_wfhashmap_map") {
    //   tervel::Tervel m_tervel(3); // 3 threads: main, setter, getter
    //   auto m_context = new tervel::ThreadContext(&m_tervel);

    //   typedef tervel::containers::wf::HashMap<uint64_t, uint64_t> map_t;
    //   CXLBench<map_t> bench(dsSize, dsNumaNode, setterNumaNode,
    //   getterNumaNode,
    //                         setterCore, getterCore);
    //   bench.init();
    //   bench.run(loopRounds, &m_tervel);
    //   bench.clean();

    //   delete m_context;
  } else if (dsType == "junction_leapfrogmap_map") {
    junction::QSBR::Context context = junction::DefaultQSBR.createContext();

    typedef junction::ConcurrentMap_Leapfrog<uint64_t, uint64_t> map_t;
    CXLBench<map_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                          setterCore, getterCore);
    bench.init(context);
    bench.run(loopRounds);
    bench.clean();

    junction::DefaultQSBR.destroyContext(context);
  } else if (dsType == "junction_grampamap_map") {
    junction::QSBR::Context context = junction::DefaultQSBR.createContext();

    typedef junction::ConcurrentMap_Grampa<uint64_t, uint64_t> map_t;
    CXLBench<map_t> bench(dsSize, dsNumaNode, setterNumaNode, getterNumaNode,
                          setterCore, getterCore);
    bench.init(context);
    bench.run(loopRounds);
    bench.clean();

    junction::DefaultQSBR.destroyContext(context);
  } else {
    std::cerr << "Data structure type is not supported!" << std::endl;
  }

  return 0;
}

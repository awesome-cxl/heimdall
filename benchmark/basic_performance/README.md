# Basic Performance

## 1. Configure the machine environment files

Heimdall needs two configuration files to understand the test environment:

1. Create the user configuration file, ***`USER_PASSWORD` field is mandatory*** while others are optional
   ```shell
   cd benchmark/basic_performance/env_files
   nano self_template.env
   mv self_template.env self.env
   ```

2. Create the machine configuration file ***All fields are required in this file***
   ```shell
   cd benchmark/basic_performance/env_files
   nano machine_template.env
   mv machine_template.env $(hostname).env
   ```

## 2. [Recommended] Modify/create the test sciript

Next, we will create tests script to configure the BW vs Latency and Cache Latency tests.

### Bandwidth vs Latency Test

Configure the bandwidth vs latency test script:

 ```bash
 cd benchmark/basic_performance/scripts/batch
 nano 100_{your test script}.yaml # or reuse previous one 100_bw_vs_latency.yaml, etc..
 ```

 **Fields**

 1. Thread number & Thread number type configuration:  
    - `thread_num_type`:
      - `0`: user defined thread number, specify the thread number in `thread_num_array`
      - `1`: auto detect thread number, in this mode, thread number will be detected automatically and sweep the thread number from 1 to the detected thread number
    - `thread_num_array`:
      - Specify how many thread to use in the test
      - **Warning**: Don't overflow the number of cores in the machine
      - **Example**: In this case, we sweep the thread count between 1 and 3 and run the test
       ```yaml
       thread_num_array: [1, 2, 3]
       ```
 2. `pattern_iteration_array` configuration:
    - specify how many time iteration to run the random pointer chasing
 3. `thread_buffer_size` array_megabyte configuration:
    - specify the buffer size for each thread
 4. `numa_node_array` configuration:
    - specify the numa node to use
 5. `core_socket_array` configuration:
    - specify the core to use
 6. `loadstore_array` configuration:
    - `0`: load
    - `1`: store

### Cache Analysis Test

```bash
 cd benchmark/basic_performance/scripts/batch
 nano 200_{your test script}.yaml # or reuse 200_cache_heatmap.yaml
```

 **Fields**
 1. `repeat` configuration:
    - specify the number of pointer-chasing rounds
 2. `test_type` configuration:
    - `0`: measure load/store operation latency
    - `1`: measure flush operation latency if `use_flush` is set to `1`
 3. `use_flush` configuration:
    - `0`: no flushing
    - `1`: flush data after each round of pointer-chasing
 4. `flush_type` configuration:
    - select the type of flush instruction:
      - `0`: clflush
      - `1`: clflushopt
      - `2`: clwb
 5. `ldst_type` configuration:
    - select the type of load/store instruction:
      - `0`: regular
      - `1`: non-temporal (will add support soon)
      - `2`: atomic (will add support soon)
 6. `core_id` configuration:
    - specify the core to run benchmark
 7. `node_id` configuration:
    - specify the accessed memory node
 8. `access_order` configuration:
    - `0`: random pointer-chasing
    - `1`: sequential pointer-chasing
 9. `stride_size_array` configuration:
    - specify the stride size between two sequential memory blocks
 10. `block_num_array` configuration:
      - specify the number of accessed memory blocks


### Cache Analysis Setup Instructions

To ensure accurate and repeatable cache analysis results, we use a pointer-chasing benchmark executed on a contiguous physical address range. Since physical addresses are accessible only in kernel mode, a kernel module is designed to perform the cache analysis.

#### Configuration Steps

1. **Specify Physical Address Ranges**  
   Before running the cache analysis, define the physical address ranges for both DIMM and CXL memory in the `$(hostname).env` file. Example configuration:

   ```
   dimm_physical_start_addr=0x800000000  # 32GB
   cxl_physical_start_addr=0x4080000000  # 258GB
   test_size=0x840000000  # 33GB (32GB test buffer + 1GB cindex buffer)
   ```

   - For DIMM memory testing, the physical address range is set from 32GB to 65GB.
   - For CXL memory testing, the CXL node starts at the physical address 258GB.
   - To obtain the physical address range of each NUMA node, navigate to the `benchmark/basic_performance/build/cache_test/misc/numa_info` directory and execute the `make` command.

2. **Reserve Physical Address Range**  
   To prevent system crashes when accessing physical addresses directly, reserve the specified physical address range using the `memmap` kernel boot parameter. For example, add the following to the Linux boot command:

   ```
   memmap=33G!32G
   ```

   This reserves a 33GB range starting at 32GB for safe testing.

## 3. Start the test

For the bandwidth vs latency test

```bash
cd ${HEIMDALL_ROOT}
uv run heimdall bench build basic bw
uv run heimdall bench run basic bw
```

For the cache analysis test

```bash
cd ${HEIMDALL_ROOT}
uv run heimdall bench build basic cache
uv run heimdall bench run basic cache
```

## 4. Check the result

For the bandwidth vs latency test

```bash
cd ${HEIMDALL_ROOT}/results/basic_performance/100
```

For the cache analysis test

```bash
cd ${HEIMDALL_ROOT}/results/basic_performance/200
```

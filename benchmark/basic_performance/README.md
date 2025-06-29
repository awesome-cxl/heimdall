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

# Heimdall: Heterogeneous Memory Benchmark Suite

## Usage

Install tools:

```shell
$ pip3 install poetry pre-commit
```

Activate the poetry python environement and execute the heimdall command line.

```shel
$ poetry install

$ poetry run heimdall --help
```

When developing code, use pre-commit to format commits:

```shell
$ pre-commit install
```

**If you need a portable standalone executable of heimdall** (in case your experiment machine does not have internet or cannot install python packages), then:

```shell
$ make standalone
# It builds the executable 'heimdall' under 'dist' dir

$ cd ..
$ tar -zcvf heimdall.tar.gz heimdall/
$ scp heimdall.tar.gz <remote-machine>
```

And then ssh to your machine:

```shell
# Run heimdall standalone binary with all the source files from heimdall git repo
[remote-machine] $ tar -zxvf heimdall.tar.gz
[remote-machine] $ cd heimdall
[remote-machine] $ ./dist/heimdall <sub-commands>

# Make sure the heimdall source repo is copied with the standalone binary,
# because all the C/C++ source code are needed and they are not part of the
# standalone binary
```

## Basic Performance

### 1. Clone the code

```shell
$ git clone --recurse-submodules git@github.com:awesome-cxl/heimdall.git
```

### 2. Install dependencies

```shell
$ cd heimdall
$ poetry install
```

### 3. Make Environment files

Make the user's env file

***`USER_PASSWORD` field is mandatory***

```shell
$ cd benchmark/basic_performance/env_files
$ nano self_template.env
$ mv self_template.env self.env
```
Make the machine's env file

***ALL fields are required***

```shell
$ cd benchmark/basic_performance/env_files
$ nano machine_template.env
$ mv machine_template.env {hostname}.env
```

if you don't know the hostname, you can use the following command to get it:


```shell
$ hostname
```
### 4. [Recommended] Modify/make the test sciript

For bandwidth vs latency test

 ```bash
 $ cd benchmark/basic_performance/scripts/batch
 $ nano 100_{your test script}.yaml or reuse previous one 100_bw_vs_latency.yaml, etc..
 ```
 1. Thread number & Thread number type configuration:
    - 'thread_num_type':
      - `0`: user defined thread number, specify the thread number in `thread_num_array`
      - `1`: auto detect thread number, in this mode, thread number will be detected automatically and sweep the thread number from 1 to the detected thread number 
   - 'thread_num_array':
      - Specify how many thread to use in the test
      - **Warning**: Don't overflow the number of cores in the machine
      - Example: In this case, we change the thread number from 1 to 3 and conduct the test
       ```yaml
       thread_num_array: [1, 2, 3]
       ```
 2. `pattern_iteration_array` configuration:
    - specify how many time iteration to run the random pointer chasing
 3. `thread_buffer_size` array_megabyte configuration:
    - specify the buffer size for each thread
 4. numa_node_array configuration:
    1. specify the numa node to use
 5. core_socket_array configuration:
    1. specify the core to use 
 6. `loadstore_array` configuration:
    - `0`: load
    - `1`: store

For cache analysis test

```bash
 $ cd benchmark/basic_performance/scripts/batch
 $ nano 200_{your test script}.yaml or reuse previous one 200_cache_heatmap.yaml
```

### 5. Start the test

For bandwidth vs latency test

```bash
$ cd {top directory}
$ poetry run heimdall bench build basic bw
$ poetry run heimdall bench run basic bw
```

For cache analysis test

```bash
$ cd {top directory}
$ poetry run heimdall bench build basic cache
$ poetry run heimdall bench run basic cache
```

### 6. Check the result

For bandwidth vs latency test

```bash
$ cd {top directory}/results/basic_performance/100
```

For cache analysis test

```bash
$ cd {top directory}/results/basic_performance/200
```

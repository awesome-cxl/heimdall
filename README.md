# Heimdall: Heterogeneous Memory Benchmark Suite

## Usage

Install tools:

```shell
$ pip3 install poetry pre-commit
```

Activate the poetry python environement and execute the heimdall command line.

```shel
$ poetry install

$ heimdall --help
```

When developing code, use pre-commit to format commits:

```shell
$ pre-commit install
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

### 3. Make Environment files (required)

Make the user's env file

***USER_PASSWORD field is mandatory***

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
### 4. Make the test sciript(if you need)

For bandwidth vs latency test

 ```bash
 $ cd benchmark/basic_performance/scripts/batch
 $ nano 100_{your test script}.yaml or reuse previous one 100_bw_vs_latency.yaml, etc.. 
 ```
 1. thread number configuration 
    1. specify how many thread to use in the test
    2. ```don't overflow the number of cores in the machine```
    3. Example:
       1. in this case, we change the thread number from 1 to 3 and conduct the test
    ```yaml
      thread_num_array: [1, 2, 3]
      ```
 2. pattern_iteration_array configuration:
    1. specify how many time iteration to run the random pointer chasing
 3. thread_buffer_size array_megabyte configuration:
    1. specify the buffer size for each thread
 4. access_type_array configuration:
    1. 0: local node
    2. 1: remote node
 5. memory_device_array configuration:
    1. 0: cxl device
    2. 1: dimm
 6. loadstore_array configuration:
    1. 0: load
    2. 1: store

For cache analysis test

```bash
 $ cd benchmark/basic_performance/scripts/batch
 $ nano 200_{your test script}.yaml or reuse previous one 200_cache_heatmap.yaml
```

### 5. Start the test

For bandwidth vs latency test

```bash
$ cd {top directory}/heimdall
$ poetry run python3 ./bench.py all basic bw
```

For cache analysis test

```bash
$ cd {top directory}/heimdall
$ poetry run python3 ./bench.py all basic cache
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











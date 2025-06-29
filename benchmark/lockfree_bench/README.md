# Lockfree Bench

## Usage

1. Install dependencies:
    ```shell
    USER_PASSWORD=password uv run heimdall bench install lockfree all
    ```

2. Build benchmark
    ```shell
    USER_PASSWORD=password uv run heimdall bench build lockfree all
    ```

3. Run benchmark
    ```shell
    USER_PASSWORD=password uv run heimdall bench run lockfree <machine_name>
    ```

Before running the benchmark, please add configuration of the machine in `run_bench.py`. The configuration is stored in map `numa_configs`. The key is the `machine_name` in running command. Values' meaning is in the comment of the map.

After running the benchmark, logs, raw results in json format and plots will be stored in the `results` subdirectory in the `lockfree_bench` directory.

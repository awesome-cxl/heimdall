[![Tests](https://github.com/awesome-cxl/heimdall/actions/workflows/build.yaml/badge.svg?branch=main)](https://github.com/awesome-cxl/heimdall/actions/workflows/build.yaml)

# Heimdall: Heterogeneous Memory Benchmark Suite

Heimdall is a benchmark suite to profile the heterogeneous memory systems, including systems with CXL, NVLink-C2C, and AMD Infinity Fabric. See [our paper](https://arxiv.org/abs/2411.02814) for our profiling results of CXL, NVLink-C2C, and AMD Infinity Fabric, by using Heimdall.

## Usage

To install and use Heimdall, please follow these instructions. Currently, Heimdall is supported on Ubuntu 22.04.

> While it is possible to run the benchmarks on other platforms, non Ubuntu/Debian-based distributions would require manually installing the dependencies (search the repo for `apt` to see all such dependencies).

### Install dependencies
1. Clone the repo:  
      ```console
      $ git clone 'https://github.com/awesome-cxl/heimdall.git' --recursive
      ```
2. Install `uv`:
      ```console
      # Refer to https://docs.astral.sh/uv/getting-started/installation/
      $ curl -LsSf https://astral.sh/uv/install.sh | sh
      ```
3. Activate the uv python environment and execute the heimdall command line.
      ```console
      $ uv run heimdall --help
      ```

4. [Optional] When developing code, use pre-commit to format commits:
      ```console
      $ pip install pre-commit
      $ pre-commit install
      ```

### Run Benchmarks

Benchmarks are implemented under the `benchmark/` sub dir. Check each benchmark's doc for example usages:

1. [Basic Performance](./benchmark/basic_performance/README.md)
2. [Lock-Free Datastructure](./benchmark/lockfree_bench/README.md)
3. [LLM](./benchmark/llm_bench/README.md)

## Citation

```bibtex
@misc{Heimdall,
      title={The Hitchhiker's Guide to Programming and Optimizing Cache Coherent Heterogeneous Systems: CXL, NVLink-C2C, and AMD Infinity Fabric},
      author={Zixuan Wang and Suyash Mahar and Luyi Li and Jangseon Park and Jinpyo Kim and Theodore Michailidis and Yue Pan and Mingyao Shen and Tajana Rosing and Dean Tullsen and Steven Swanson and Jishen Zhao},
      year={2024},
      eprint={2411.02814},
      archivePrefix={arXiv},
      primaryClass={cs.PF},
      url={https://arxiv.org/abs/2411.02814},
}
```

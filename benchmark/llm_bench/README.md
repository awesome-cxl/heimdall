# LLM Benchmark

LLM benchmark module for heimdall. This module allows you to measure and compare the performance of various LLM inference frameworks (PyTorch, Llama.cpp, vLLM).

## Supported Frameworks

- **PyTorch**: CPU inference using Meta's official Llama3 implementation
- **Llama.cpp**: Efficient CPU inference with quantized models
- **vLLM**: High-performance inference serving for both CPU and GPU (v0.9.1)

## Prerequisites

1. **Hugging Face Login**
   ```bash
   huggingface-cli login
   ```

2. **Basic Package Installation**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y numactl git-lfs
   
   # For vLLM CPU (additional requirements)
   sudo apt-get install -y gcc-12 g++-12 libnuma-dev python3-dev
   sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 10 --slave /usr/bin/g++ g++ /usr/bin/g++-12
   ```



## Quick Start

### 1. Installation

Install each framework separately (automatically manages virtual environments):

```bash
# Install PyTorch (includes Llama3-8B model)
uv run heimdall bench install llm pytorch

# Install Llama.cpp (includes quantized model)
uv run heimdall bench install llm llamacpp

# Install vLLM CPU (builds from source with v0.9.1)
uv run heimdall bench install llm vllm_cpu

# Install vLLM GPU
uv run heimdall bench install llm vllm_gpu
```

### 2. Run Benchmarks

```bash
# Run PyTorch benchmark
uv run heimdall bench run llm pytorch

# Run Llama.cpp benchmark
uv run heimdall bench run llm llamacpp

# Run vLLM CPU benchmark
uv run heimdall bench run llm vllm_cpu

# Run vLLM GPU benchmark
uv run heimdall bench run llm vllm_gpu

# Run all benchmarks
uv run heimdall bench run llm all

# Generate plots from results
uv run heimdall bench plot llm all
```

## Virtual Environment Management

The benchmark system automatically manages Python virtual environments:

- **Automatic Creation**: Creates `.venv` in the project root if it doesn't exist
- **Automatic Activation**: All commands run within the virtual environment
- **Python 3.12**: Uses Python 3.12 with `uv` for optimal performance
- **Isolation**: Each framework installation is isolated and doesn't conflict

Manual virtual environment usage:
```bash
# Activate virtual environment manually
source .venv/bin/activate

# Check virtual environment status
which python
```

## Detailed Usage

### PyTorch

#### Throughput Benchmark
```bash
# Direct script execution
bash benchmark/llm_bench/scripts/pytorch_run_test.sh
```

#### Performance Profiling
```bash
# Detailed performance analysis using perf
bash benchmark/llm_bench/scripts/pytorch_perf_test.sh
```

Measured metrics:
- Tokens per second
- Latency per token
- Hardware performance counters (CPU cycles, cache misses, etc.)

### Llama.cpp

```bash
# Benchmark using quantized model
bash benchmark/llm_bench/scripts/llamacpp_run_test.sh
```

Features:
- Uses Q4_K_M quantized Meta-Llama-3-8B model
- Efficient inference with low memory usage

### vLLM

#### CPU Mode (v0.9.1)
```bash
# CPU-based inference benchmark
bash benchmark/llm_bench/scripts/vllm_run_test.sh
```

Environment variables:
- `VLLM_CPU_KVCACHE_SPACE=30`: KV cache space configuration
- `LD_PRELOAD`: Memory optimization using tcmalloc
- `VLLM_TARGET_DEVICE=cpu`: Force CPU-only mode
- `CUDA_VISIBLE_DEVICES=""`: Disable CUDA

#### GPU Mode
```bash
# GPU-based inference benchmark (Meta-Llama-3-70B)
bash benchmark/llm_bench/scripts/vllm_gpu_run_test.sh
```

Features:
- Support for large models (70B)
- Memory efficiency through CPU offloading

## vLLM Installation Details

### CPU Mode (Source Build - v0.9.1)

vLLM CPU installation automatically builds from source with the following process:

### Independent Installation (Alternative)

If heimdall installation fails, you can install independently:

> 🔗 **Reference**: For the latest installation methods, check the [Official vLLM CPU Installation Documentation](https://docs.vllm.ai/en/stable/getting_started/installation/cpu.html).



## NUMA Configuration

All benchmarks support NUMA node-specific performance measurement:

- **Node 0**: DIMM memory
- **Node 2**: CXL memory
- **CPU Binding**: Local/remote memory access pattern analysis

Measurement combinations:
1. No CPU Bind, Node 0 (DIMM)
2. No CPU Bind, Node 2 (CXL)
3. CPU 0, Node 0 (Local DIMM)
4. CPU 1, Node 0 (Remote DIMM)
5. CPU 0, Node 2 (Local CXL)
6. CPU 1, Node 2 (Remote CXL)

## Result Analysis

### Log Files
Benchmark results are saved in the following locations:
```
benchmark/llm_bench/logs/
├── pytorch/
│   └── test_results.csv
├── llamacpp/
│   └── test_results.csv
├── vllm/
│   └── test_results.csv
└── vllm_gpu/
    └── test_results.csv
```

### Plot Generation
```bash
# Visualize results
python benchmark/llm_bench/src/plot_maker.py
```

Generated plots:
- `benchmark/llm_bench/logs/plot/figure_*_test_results.png`

## Datasets

Used datasets:
- **Wikipedia test data**: `benchmark/llm_bench/datasets/wiki.test.raw`
- **ShareGPT v3**: `benchmark/llm_bench/datasets/ShareGPT_V3_unfiltered_cleaned_split.json` (for vLLM)

## Models

### PyTorch
- **Model**: Meta-Llama-3-8B
- **Path**: `benchmark/llm_bench/models/meta-llama/Meta-Llama-3-8B/`
- **Format**: Original PyTorch checkpoints

### Llama.cpp
- **Model**: Meta-Llama-3-8B.Q4_K_M.gguf
- **Path**: `benchmark/llm_bench/models/QuantFactory/`
- **Format**: 4-bit quantized GGUF

### vLLM
- **CPU**: Meta-Llama-3-8B (v0.9.1)
- **GPU**: Meta-Llama-3-70B
- **Source**: Automatic download from Hugging Face Hub

## Troubleshooting

### Common Issues

1. **Hugging Face Login Error**
   ```bash
   huggingface-cli login
   ```

2. **Memory Shortage**
   - Ensure sufficient RAM for model size (32GB+ for 8B models)
   - Sufficient VRAM required for vLLM GPU mode

3. **Check NUMA Configuration**
   ```bash
   numactl --hardware
   ```

4. **Permission Issues**
   - Permission settings required for perf commands

5. **uv Command Not Found**
   ```bash
   # uv should be available as part of heimdall setup
   # If missing, check heimdall installation
   export PATH="$HOME/.local/bin:$PATH"
   ```

### vLLM Specific Issues

#### CPU Mode Build Errors
```bash
# Compiler issues
sudo apt-get install -y gcc-12 g++-12 libnuma-dev python3-dev
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 10 --slave /usr/bin/g++ g++ /usr/bin/g++-12

# CMake version issues
pip install "cmake>=3.26.1"

# Memory issues during build
export MAX_JOBS=4  # Limit parallel build jobs
```

#### Environment Configuration
For optimal performance in CPU mode:
```bash
export VLLM_CPU_KVCACHE_SPACE=30
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4
export VLLM_TARGET_DEVICE=cpu
export CUDA_VISIBLE_DEVICES=""
```

## Additional Scripts

### Independent Execution Scripts
- `benchmark/llm_bench/scripts/run.py`: Simple task runner
- `benchmark/llm_bench/src/pytorch_run_test.py`: PyTorch test execution
- `benchmark/llm_bench/src/pytorch_perf_profile.py`: Performance profiling

### Usage Examples
```bash
# Direct PyTorch test execution
cd benchmark/llm_bench/llama
python pytorch_run_test.py --cpu_bind 0 --mem_bind 0 --description "Local DIMM"

# Manual virtual environment usage
source .venv/bin/activate
python benchmark/llm_bench/src/vllm_run_test.py
```

## Version Information

- **vLLM**: v0.9.1 (CPU source build)
- **PyTorch**: 2.7.0+cpu (for vLLM CPU)
- **Python**: 3.12 (recommended)
- **uv**: Latest (for package management) 
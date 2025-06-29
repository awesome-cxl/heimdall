# LLM Benchmark

LLM benchmark module for heimdall. This module allows you to measure and compare the performance of various LLM inference frameworks (PyTorch, Llama.cpp, vLLM).

## Supported Frameworks

- **PyTorch**: CPU inference using Meta's official Llama3 implementation
- **Llama.cpp**: Efficient CPU inference with quantized models
- **vLLM**: High-performance inference serving for both CPU and GPU

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
   ```

## Quick Start

### 1. Installation

Install each framework separately:

```bash
# Install PyTorch (includes Llama3-8B model)
uv run heimdall bench install llm pytorch

# Install Llama.cpp (includes quantized model)
uv run heimdall bench install llm llamacpp

# Install vLLM CPU
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

#### CPU Mode
```bash
# CPU-based inference benchmark
bash benchmark/llm_bench/scripts/vllm_run_test.sh
```

Environment variables:
- `VLLM_CPU_KVCACHE_SPACE=30`: KV cache space configuration
- `LD_PRELOAD`: Memory optimization using tcmalloc

#### GPU Mode
```bash
# GPU-based inference benchmark (Meta-Llama-3-70B)
bash benchmark/llm_bench/scripts/vllm_gpu_run_test.sh
```

Features:
- Support for large models (70B)
- Memory efficiency through CPU offloading

## vLLM Independent Installation

vLLM installation through heimdall may fail depending on individual environments. In such cases, you can install it independently:

### CPU Mode
```bash
pip install vllm[cpu]
# Or build from source
git clone https://github.com/vllm-project/vllm.git
cd vllm
pip install -e .
```

### GPU Mode
```bash
pip install vllm
```

After independent installation, you can run benchmarks by executing the scripts directly.

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
- **CPU**: Meta-Llama-3-8B
- **GPU**: Meta-Llama-3-70B
- **Source**: Automatic download from Hugging Face Hub

## Troubleshooting

### Common Issues

1. **Hugging Face Login Error**
   ```bash
   huggingface-cli login
   ```

2. **Memory Shortage**
   - Ensure sufficient RAM for model size
   - Sufficient VRAM required for vLLM GPU mode

3. **Check NUMA Configuration**
   ```bash
   numactl --hardware
   ```

4. **Permission Issues**
   - Permission settings required for perf commands

### vLLM Special Configuration

For optimal performance in CPU mode, set the following environment:
```bash
export VLLM_CPU_KVCACHE_SPACE=30
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4
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
``` 
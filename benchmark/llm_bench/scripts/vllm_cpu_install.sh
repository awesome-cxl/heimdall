#!/bin/bash
set -e

echo "Current directory: $(pwd)"
echo "Script location: $(dirname $0)"

# Get the base directory (heimdall-1)
BASE_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
echo "Base directory: $BASE_DIR"

# Create Python virtual environment if not exists
if [ ! -d "$BASE_DIR/.venv" ]; then
  # Prepare Python environment
  cd "$BASE_DIR"
  uv venv --python 3.12 --seed
fi

cd "$BASE_DIR"
source .venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install "cmake>=3.26.1" wheel packaging ninja "setuptools-scm>=8" numpy

# Move to vllm_cpu directory (which contains the vLLM source)
cd "$BASE_DIR/benchmark/llm_bench/vllm_cpu"

# Install CPU backend dependencies
pip install -v -r requirements/cpu.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Build and install vLLM for CPU
VLLM_TARGET_DEVICE=cpu python setup.py install 
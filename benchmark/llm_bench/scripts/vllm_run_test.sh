#!/bin/bash

# This script runs the throughput benchmark for VLLM with different NUMA configurations.
# It uses the `numactl` command to bind the process to specific CPUs and memory nodes.
# The results are saved in separate JSON files for each NUMA configuration.

# Set environment variables for CPU KV cache space and LD_PRELOAD
# if you are using GPU, you can set VLLM_GPU_KVCACHE_SPACE instead
export VLLM_CPU_KVCACHE_SPACE=30
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4:$LD_PRELOAD

# Set the Hugging Face cache directory
export HF_HOME="../cache/huggingface"

NUMA_CONFIGS=(
	"--membind=0"
	"--membind=2"
	"--cpubind=0 --membind=0"
	"--cpubind=0 --membind=2"
	"--cpubind=1 --membind=0"
	"--cpubind=1 --membind=2"
)

VLLM_PATH="benchmark/llm_bench/vllm"
MODEL="benchmark/llm_bench/cache/huggingface/Meta-Llama-3-8B-Instruct"
DATASET="benchmark/llm_bench/datasets/ShareGPT_V3_unfiltered_cleaned_split.json"

# Define the vllm function
vllm() {
	local numa_config="$1"

	# Extract cpu_bind and mem_bind
	local cpu_bind="default"
	local mem_bind

	if [[ $numa_config =~ --cpubind=([0-9]+) ]]; then
		cpu_bind="cpu${BASH_REMATCH[1]}"
	fi

	if [[ $numa_config =~ --membind=([0-9]+) ]]; then
		mem_bind="${BASH_REMATCH[1]}"
	else
		mem_bind="none"
	fi

	mem_bind=$(echo "$numa_config" | grep -oP "(?<=--membind=)\d+" || echo "none")

	local output_json="KV30_result_cpu${cpu_bind}_mem${mem_bind}.json"

	echo "NUMA Config: $numa_config"
	echo "CPU Bind: $cpu_bind"
	echo "Mem Bind: $mem_bind"
	echo "Output JSON: $output_json"

	numactl "$numa_config" python $VLLM_PATH/benchmarks/benchmark_throughput.py \
		--model $MODEL \
		--dataset $DATASET \
		--output-json "$output_json"

	sleep 2
}

# Loop through NUMA configurations and call vllm
for numa_config in "${NUMA_CONFIGS[@]}"; do
	vllm "$numa_config"
done

echo "Finished running VLLM throughput benchmark"

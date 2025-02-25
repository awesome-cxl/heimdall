#!/bin/bash

# Define the model and file paths
MODEL_PATH="benchmark/llm_bench/models/QuantFactory/Meta-Llama-3-8B.Q4_K_M.gguf"
FILE_PATH="benchmark/llm_bench/datasets/wiki.test.raw"
LOG_DIR="benchmark/llm_bench/logs/llamacpp"
LLAMA_CPP_PATH="benchmark/llm_bench/llama.cpp/build/bin/"

mkdir -p $LOG_DIR

# Define the numactl command with different NUMA nodes
NUMA_NODES=(0 1 2)
CPU_BIND_OPTIONS=(0 1)

# Loop through each NUMA node and execute the command
for NODE in "${NUMA_NODES[@]}"; do
	for CPU_BIND in "${CPU_BIND_OPTIONS[@]}"; do
		output_file="${LOG_DIR}/llamacpp_numa_node_${NODE}_cpubind_${CPU_BIND}.csv"
		# Create CSV header with metric and value columns
		echo "metric,value" >"$output_file"
		echo "Running on NUMA node $NODE with CPU bind to NUMA node $CPU_BIND"

		numactl --membind="$NODE" --cpubind="$CPU_BIND" \
			"$LLAMA_CPP_PATH/llama-perplexity" -m $MODEL_PATH \
			-f $FILE_PATH >>"$output_file" 2>&1
	done
done

echo "Finished running llamacpp throughput benchmark"

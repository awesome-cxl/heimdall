#!/bin/bash

# This script runs the throughput benchmark for VLLM with different NUMA configurations.
# It uses the numactl command to bind the process to DIMM and CXL.
# The results are saved in separate JSON files for each NUMA configuration.
# The model is Meta-Llama-3-70B and offload size is 90GB.

HUGGING_FACE_HUB_TOKEN=$(cat ~/.cache/huggingface/token)
export HUGGING_FACE_HUB_TOKEN

# Set the Hugging Face cache directory
export HF_HOME="benchmark/llm_bench/cache/huggingface"

# Define arrays for CPU binds, memory binds, and descriptions
cpu_binds=("" "")
mem_binds=(0 2)
descriptions=(
	"No CPU Bind, Node 0 (DIMM)"
	"No CPU Bind, Node 2 (CXL)"
)

VLLM_PATH="benchmark/llm_bench/vllm_gpu"
MODEL="meta-llama/Meta-Llama-3-70B"
DATASET="benchmark/llm_bench/datasets/ShareGPT_V3_unfiltered_cleaned_split.json"
LOG_DIR="benchmark/llm_bench/logs/vllm_gpu"
offload_size="90"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Define the vllm function
vllm() {
	local cpu_bind="$1"
	local mem_bind="$2"
	local description="$3"
	local index="$4"

	# Construct NUMA command
	local numa_cmd=("numactl")
	if [[ -n $cpu_bind ]]; then
		numa_cmd+=("--cpubind=$cpu_bind")
	fi
	numa_cmd+=("--membind=$mem_bind")

	# Determine CPU bind label
	local cpu_label="nocpubind"
	if [[ -n $cpu_bind ]]; then
		cpu_label="cpu$cpu_bind"
	fi

	# Output file name
	local output_json="$LOG_DIR/GPU_result_${cpu_label}_mem${mem_bind}.json"

	echo "Index: $index"
	echo "Description: $description"
	echo "NUMA Config: ${numa_cmd[*]}"
	echo "CPU Bind: $cpu_label"
	echo "Mem Bind: $mem_bind"
	echo "Output JSON: $output_json"

	# Run the benchmark with numactl
	"${numa_cmd[@]}" python "$VLLM_PATH/benchmarks/benchmark_throughput.py" \
		--model "$MODEL" \
		--cpu_offload_gb=$offload_size \
		--dataset "$DATASET" \
		--output-json "$output_json"

	sleep 2
}

# Loop through configurations and call vllm
for i in "${!mem_binds[@]}"; do
	vllm "${cpu_binds[$i]}" "${mem_binds[$i]}" "${descriptions[$i]}" "$i"
done

# Create CSV file with pipe separator in the log directory
output_csv="$LOG_DIR/test_results.csv"

# Write CSV header with pipe separator
echo "cpu|mem|tokens_per_sec" >"$output_csv"

# Extract data from JSON files and convert to CSV
for json_file in "$LOG_DIR"/GPU_result_*_mem*.json; do
	if [[ -f $json_file ]]; then
		# Extract cpu and mem from filename
		cpu=$(echo "$json_file" | grep -oP "(?<=GPU_result_)[a-z0-9]+" | grep -oP "(?<=cpu)[0-1]|nocpubind")
		mem=$(echo "$json_file" | grep -oP "(?<=mem)[0-2]")

		# Extract tokens_per_second from JSON
		tokens_per_sec=$(grep "tokens_per_second" "$json_file" | awk -F: '{print $2}' | tr -d ' ,"')
		if [[ -z $tokens_per_sec ]]; then
			tokens_per_sec="N/A"
		else
			# Format the tokens_per_sec value to 2 decimal places if it's numeric
			tokens_per_sec=$(printf "%.2f" "$tokens_per_sec")
		fi

		# Append line to CSV with pipe separator
		echo "$cpu|$mem|$tokens_per_sec" >>"$output_csv"
	fi
done

# Notify completion
echo "CSV file '$output_csv' has been generated"
echo "Finished running VLLM throughput benchmark"

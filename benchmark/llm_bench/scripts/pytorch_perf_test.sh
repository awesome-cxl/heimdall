#!/bin/bash

# Set output directory for logs and create it if it doesn't exist
output_dir="benchmark/llm_bench/logs/pytorch"
mkdir -p "$output_dir"

# Define CPU bindings, memory bindings, and their descriptions
cpu_binds=("" "" 0 1 0 1)
mem_binds=(0 2 0 0 2 2)
descriptions=(
	"No CPU Bind, Node 0 (DIMM)"
	"No CPU Bind, Node 2 (CXL)"
	"CPU 0, Node 0 (Local DIMM)"
	"CPU 1, Node 0 (Remote DIMM)"
	"CPU 0, Node 2 (Local CXL)"
	"CPU 1, Node 2 (Remote CXL)"
)

# Loop over each configuration and run the performance profile script
for i in "${!mem_binds[@]}"; do
	cpu_bind=${cpu_binds[$i]}
	mem_bind=${mem_binds[$i]}
	description=${descriptions[$i]}

	# Use "nocpubind" if cpu_bind is empty
	# cpu_label=${cpu_bind:-nocpubind}

	echo "Running with CPU binding: ${cpu_bind:-None}, Memory binding: ${mem_bind} (${description})"

	# If cpu_bind is empty, set cpu_bind_value to -1 (default) and do not pass --cpubind.
	if [ -z "${cpu_bind}" ]; then
		cpu_bind_value=-1
		echo "Running with CPU binding: ${cpu_bind_value}, Memory binding: ${mem_bind} (${description})"
		if ! numactl --membind="${mem_bind}" torchrun --nproc_per_node=1 benchmark/llm_bench/llama/pytorch_perf_profile.py \
			"${cpu_bind_value}" "${mem_bind}"; then
			echo "Error: pytorch_perf_profile script failed without CPU binding"
		fi
	else
		cpu_bind_value=${cpu_bind}
		echo "Running with CPU binding: ${cpu_bind_value}, Memory binding: ${mem_bind} (${description})"
		if ! numactl --cpubind="${cpu_bind_value}" --membind="${mem_bind}" torchrun --nproc_per_node=1 benchmark/llm_bench/llama/pytorch_perf_profile.py \
			"${cpu_bind_value}" "${mem_bind}"; then
			echo "Error: pytorch_perf_profile script failed with CPU binding"
		fi
	fi
done

echo "Finished running PyTorch performance profile benchmark"

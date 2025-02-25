#!/bin/bash

output_dir="benchmark/llm_bench/logs/pytorch"
mkdir -p "$output_dir"

cpu_binds=(0 1 0 1 "" "")
mem_binds=(0 0 2 2 0 2)
descriptions=(
	"CPU 0, Node 0 (Local DIMM)"
	"CPU 1, Node 0 (Remote DIMM)"
	"CPU 0, Node 2 (Local CXL)"
	"CPU 1, Node 2 (Remote CXL)"
	"No CPU Bind, Node 0 (DIMM)"
	"No CPU Bind, Node 2 (CXL)"
)

for i in "${!mem_binds[@]}"; do
	cpu_bind=${cpu_binds[$i]}
	mem_bind=${mem_binds[$i]}
	description=${descriptions[$i]}

	cpu_label=${cpu_bind:-nocpubind}
	output_file="${output_dir}/pytorch_numa_node_${mem_bind}_cpubind_${cpu_label}.csv"

	echo "cpu_bind,mem_bind,description,latency" >"$output_file"
	echo "Running with CPU binding: ${cpu_bind:-None}, Memory binding: ${mem_bind} (${description})" >>"${output_file}"

	if [ -z "${cpu_bind}" ]; then
		if ! numactl --membind="${mem_bind}" torchrun --nproc_per_node=1 benchmark/llm_bench/llama/pytorch_run_test.py \
			--cpu_bind "${cpu_bind}" --mem_bind "${mem_bind}" --description "${description}" >>"${output_file}" 2>&1; then
			echo "Error: pytorch_run_test script failed without cpu_bind"
		fi
	else
		if ! numactl --cpubind="${cpu_bind}" --membind="${mem_bind}" torchrun --nproc_per_node=1 benchmark/llm_bench/llama/pytorch_run_test.py \
			--cpu_bind "${cpu_bind}" --mem_bind "${mem_bind}" --description "${description}" >>"${output_file}" 2>&1; then
			echo "Error: pytorch_run_test script failed with cpu_bind"
		fi
	fi
done

echo "Finished running PyTorch throughput benchmark"

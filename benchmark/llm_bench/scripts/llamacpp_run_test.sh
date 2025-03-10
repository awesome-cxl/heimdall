#!/bin/bash

# Define the model and file paths
MODEL_PATH="benchmark/llm_bench/models/QuantFactory/Meta-Llama-3-8B.Q4_K_M.gguf"
FILE_PATH="benchmark/llm_bench/datasets/wiki.test.raw"
LOG_DIR="benchmark/llm_bench/logs/llamacpp"
LLAMA_CPP_PATH="benchmark/llm_bench/llama.cpp/build/bin/"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Define combinations for testing
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

# Loop through each combination and run the test
for i in "${!mem_binds[@]}"; do
    cpu_bind=${cpu_binds[$i]}
    mem_bind=${mem_binds[$i]}
    description=${descriptions[$i]}

    # Generate output filename based on cpu_bind presence
    if [[ -z "$cpu_bind" ]]; then
        output_file="${LOG_DIR}/llamacpp_numa_node_${mem_bind}_nocpubind.csv"
    else
        output_file="${LOG_DIR}/llamacpp_numa_node_${mem_bind}_cpubind_${cpu_bind}.csv"
    fi

    # Execute numactl command, omitting --cpubind if cpu_bind is empty
    if [[ -z "$cpu_bind" ]]; then
        numactl --membind="$mem_bind" \
            "$LLAMA_CPP_PATH/llama-perplexity" -m "$MODEL_PATH" \
            -f "$FILE_PATH" >>"$output_file" 2>&1
    else
        numactl --membind="$mem_bind" --cpubind="$cpu_bind" \
            "$LLAMA_CPP_PATH/llama-perplexity" -m "$MODEL_PATH" \
            -f "$FILE_PATH" >>"$output_file" 2>&1
    fi
done

# Define output file for latency results
OUTPUT_FILE="$LOG_DIR/latency_results.txt"
declare -A latencies
declare -A counts

# Process each log file to calculate latency
for file in "$LOG_DIR"/llamacpp_numa_node_*_*.csv; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        mem=$(echo "$filename" | grep -oP 'numa_node_\K\d+' || echo "unknown")
        cpu=$(echo "$filename" | grep -oP 'cpubind_\K\d+' || echo "unknown")
        if [[ "$filename" =~ "nocpubind" ]]; then
            mem="nocpubind"
        fi

        tokens_per_sec=$(grep "prompt eval time" "$file" | grep -oP '\d+\.\d+(?= tokens per second)' || echo "0")

        if [[ "$tokens_per_sec" != "0" ]]; then
            latency=$(echo "scale=2; 1000 / $tokens_per_sec" | bc)

            if [[ -n "${latencies[$cpu|$mem]}" ]]; then
                latencies[$cpu|$mem]=$(echo "${latencies[$cpu|$mem]} + $latency" | bc)
                counts[$cpu|$mem]=$((counts[$cpu|$mem] + 1))
            else
                latencies[$cpu|$mem]=$latency
                counts[$cpu|$mem]=1
            fi
        fi
    fi
done

# Write results to the output file
echo "cpu|mem|average_latency" >"$OUTPUT_FILE"
for key in "${!latencies[@]}"; do
    cpu=${key%|*}
    mem=${key#*|}
    avg_latency=$(echo "scale=2; ${latencies[$key]} / ${counts[$key]}" | bc)
    echo "$cpu|$mem|$avg_latency" >>"$OUTPUT_FILE"
done

# Print completion message and display results
echo "Finished running llamacpp throughput benchmark"
cat "$OUTPUT_FILE"

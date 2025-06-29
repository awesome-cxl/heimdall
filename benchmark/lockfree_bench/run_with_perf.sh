#!/bin/bash

# Check if a program name was provided
if [ $# -eq 0 ]; then
	echo "Usage: $0 <program_name> [program_arguments...]"
	exit 1
fi

# Run the specified program with any additional arguments
"$@" &

# Get its PID
pid=$!

# Wait until it reaches the section you want to profile
# sleep X

# Record for duration (e.g., 0.5s)
perf record -F 99 -p $pid -e L1-dcache-loads,L1-dcache-load-misses,L1-dcache-stores,LLC-loads,LLC-load-misses,LLC-stores --call-graph dwarf -T -- sleep 10
# perf stat -e L1-dcache-loads,L1-dcache-load-misses,L1-dcache-stores,LLC-loads,LLC-load-misses,LLC-stores --per-thread -p $pid
# perf stat -e L1-dcache-load-misses,LLC-load-misses --per-thread -p $pid

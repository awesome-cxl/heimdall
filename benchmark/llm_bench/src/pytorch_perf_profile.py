import argparse
import os
import random
import shlex
import signal
import subprocess
import threading
import time

import torch
from llama import Llama

# Global timeout value (in seconds)
DEFAULT_TIMEOUT = 60


def load_test_data(tokenizer):
    """
    Load test data from a local file, tokenize it, and split into chunks.
    Updated to reflect the new dataset file location.
    """
    test_file = "benchmark/llm_bench/datasets/wiki.test.raw"
    max_seq_len = 128

    with open(test_file, encoding="utf-8") as file:
        test_data = file.read()
    tokens = tokenizer.encode(test_data, bos=True, eos=True)
    # Split tokens into chunks of max_seq_len tokens
    chunks = [tokens[i : i + max_seq_len] for i in range(0, len(tokens), max_seq_len)]
    return chunks


def terminate_after_timeout(perf_process, timeout):
    """
    Wait for 'timeout' seconds and then send SIGINT to the given process.
    """
    time.sleep(timeout)
    perf_process.send_signal(signal.SIGINT)


def run_inference_with_timer(generator, measurement_command, finish_callback, timeout, mode="segment"):
    """
    Unified function to run inference while performing a performance measurement.

    Parameters:
        generator: The Llama generator instance.
        measurement_command: The command (list or already split list) to start the measurement.
        finish_callback: A function to finalize the measurement process.
        timeout: Timeout (in seconds) after which the measurement process is terminated.
        mode: 'segment' for measurement over a random segment of inference.
    """
    chunks = load_test_data(generator.tokenizer)
    device = torch.device("cpu")
    generator.model.to(device)

    if mode == "segment":
        # Select a random measurement segment
        start_index = random.randint(0, 10)
        end_index = start_index + 10
        measurement_process = None
        for index, chunk in enumerate(chunks[:20]):
            if index == start_index and measurement_process is None:
                measurement_process = subprocess.Popen(
                    measurement_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            input_ids = torch.tensor(chunk).unsqueeze(0).to(device)
            with torch.no_grad():
                _ = generator.model(input_ids, start_pos=0)
            if index == end_index:
                if measurement_process is not None:
                    # Start a timer thread to terminate the measurement process after the timeout
                    timer_thread = threading.Thread(
                        target=terminate_after_timeout,
                        args=(measurement_process, timeout),
                    )
                    timer_thread.start()
                    timer_thread.join()
                    finish_callback(measurement_process)
                break
    else:
        # Additional modes can be implemented if needed
        pass


def finish_perf_stat(process, output_file):
    """
    Finalize the perf stat measurement.
    The output is already saved to the file specified in the command,
    so we simply wait for the process to finish.
    """
    process.wait()
    print(f"Perf stat results saved to {output_file}")


def finish_perf_record(process, output_file):
    """
    Finalize the perf record measurement.
    """
    process.wait()
    print(f"Perf record data saved to {output_file}")


def build_generator(ckpt_dir, tokenizer_path, max_seq_len, max_batch_size):
    """
    Build the Llama model and tokenizer.
    """
    generator = Llama.build(
        ckpt_dir=ckpt_dir,
        tokenizer_path=tokenizer_path,
        max_seq_len=max_seq_len,
        max_batch_size=max_batch_size,
        model_parallel_size=1,
    )
    return generator


def main():
    result_dir = "benchmark/llm_bench/perf_profile_result"
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    parser = argparse.ArgumentParser(description="Performance profiling script for PyTorch")
    parser.add_argument(
        "cpu_bind",
        type=int,
        nargs="?",
        default=-1,
        help="CPU binding number (default: -1, meaning no CPU binding)",
    )
    parser.add_argument(
        "mem_bind",
        type=int,
        nargs="?",
        default=0,
        help="Memory binding number (default: 0)",
    )
    parser.add_argument("--description", type=str, default="", help="Description of the configuration")
    args = parser.parse_args()

    # Updated model and tokenizer configuration to reflect new file locations
    ckpt_dir = "benchmark/llm_bench/models/meta-llama/Meta-Llama-3-8B"
    tokenizer_path = "benchmark/llm_bench/models/meta-llama/Meta-Llama-3-8B/tokenizer.model"
    max_seq_len = 128
    max_batch_size = 1

    generator = build_generator(ckpt_dir, tokenizer_path, max_seq_len, max_batch_size)

    # Parse command-line arguments for CPU and memory binding
    parser = argparse.ArgumentParser(
        description="Run perf stat and perf record measurements with specific CPU and memory binding"
    )
    parser.add_argument("cpu_bind", type=int, help="CPU binding number")
    parser.add_argument("mem_bind", type=int, help="Memory binding number")
    args = parser.parse_args()

    # Run perf stat measurements 5 times (using random segment measurement)
    for run_iteration in range(5):
        stat_output_file = f"{result_dir}/perf_stat_output_cpu{args.cpu_bind}_mem{args.mem_bind}_run{run_iteration}.txt"
        stat_events = (
            "cycles,instructions,cache-references,cache-misses,"
            "L1-dcache-load-misses,L1-dcache-loads,L1-dcache-stores,L1-icache-load-misses,"
            "LLC-load-misses,LLC-loads,LLC-store-misses,LLC-stores,"
            "branch-load-misses,branch-loads,"
            "dTLB-load-misses,dTLB-loads,dTLB-store-misses,dTLB-stores,iTLB-load-misses,"
            "node-load-misses,node-loads,"
            "branch-instructions,branch-misses,bus-cycles,"
            "cpu-cycles,mem-loads,mem-loads-aux,mem-stores"
        )
        stat_command = ["perf", "stat", "-e", stat_events, "-o", stat_output_file]
        run_inference_with_timer(
            generator,
            stat_command,
            lambda proc: finish_perf_stat(proc, stat_output_file),
            DEFAULT_TIMEOUT,
            mode="segment",
        )

    # Run perf record measurements 5 times (using random segment measurement)
    for run_iteration in range(5):
        cpu = args.cpu_bind
        mem = args.mem_bind
        # Filename includes iteration;
        record_output_file = f"{result_dir}/perf_cpu{cpu}_mem{mem}_{run_iteration}.data"
        inference_pid = os.getpid()
        record_command = (
            f"perf record -e L1-dcache-load-misses,L1-dcache-loads,L1-dcache-stores,"
            f"L1-icache-load-misses,LLC-load-misses,LLC-loads,LLC-store-misses,LLC-stores,"
            f"dTLB-load-misses,dTLB-loads,dTLB-store-misses,dTLB-stores,iTLB-load-misses,"
            f"cpu-cycles,instructions -p {inference_pid} -o {record_output_file}"
        )
        record_command_split = shlex.split(record_command)
        run_inference_with_timer(
            generator,
            record_command_split,
            lambda proc: finish_perf_record(proc, record_output_file),
            DEFAULT_TIMEOUT,
            mode="segment",
        )


if __name__ == "__main__":
    main()

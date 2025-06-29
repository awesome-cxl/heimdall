#
# MIT License
#
# Copyright (c) 2025 Jangseon Park
# Affiliation: University of California San Diego CSE
# Email: jap036@ucsd.edu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import glob
import itertools
import os
import re
import socket
import sys

import yaml
from dotenv import load_dotenv
from loguru import logger

import benchmark.basic_performance.scripts.utils.batch_cache as cache_batch
import benchmark.basic_performance.scripts.utils.dvfs as dvfs
import benchmark.basic_performance.scripts.utils.prefetch as prefetch
import benchmark.basic_performance.scripts.utils.slack as slack
import benchmark.basic_performance.scripts.utils.smt as smt
from benchmark.basic_performance.scripts.utils.sudo import run_as_sudo
from benchmark.basic_performance.scripts.utils.utils import (
    get_cpu_number,
    get_free_memsize,
    get_thread_per_core,
)
from heimdall.utils.path import get_workspace_path


def extract_task_number(file_path):
    match = re.search(r"/(\d+)_.*\.yaml$", file_path)
    if match:
        return int(match.group(1))
    else:
        logger.error("Can not find task number")
        sys.exit(1)


def load_global_env():
    host_name = socket.gethostname()
    path = get_workspace_path() / "benchmark" / "basic_performance" / "env_files" / f"{host_name}.env"
    if not os.path.isfile(path):
        logger.error(f"Error: {path} not found")
        raise Exception("Please make machine env file first @ utils/env_files")
    load_dotenv(dotenv_path=path)
    logger.info(f"hostname: {host_name}")
    logger.info(f"disabled prefetch: {os.getenv('disable_prefetch')}")
    logger.info(f"boost cpu: {os.getenv('boost_cpu')}")


def prepare_run(task_file, machine_type):
    slack.slack_notice_beg(f"start to run {task_file}")
    load_global_env()
    if machine_type == "x86" or machine_type == "mockup":
        smt.turn_on_smt()
        dvfs.control_cpu_boost()
        prefetch.control_prefetch()
    elif machine_type == "arm":
        logger.info("ARM machine")
        # smt.turn_off_smt()
        # dvfs.control_cpu_boost()
        # prefetch.control_prefetch()
    else:
        logger.error("Error: Invalid machine type")
        sys.exit(1)
    pass


def wrap_up_run(task_file, temp_file, machine_type):
    directory = get_workspace_path() / "heimdall"

    if machine_type == "x86" or machine_type == "mockup":
        prefetch.set_prefetcher("on")
    elif machine_type == "arm":
        pass
    else:
        logger.error("Error: Invalid machine type")
        sys.exit(1)

    slack.slack_notice_end(f"Finish to run {task_file}")

    if os.path.exists(temp_file):
        os.remove(temp_file)
    if not os.path.isdir(directory):
        logger.error(f"Error: Directory not found: {directory}")
        sys.exit(1)

    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    for file in txt_files:
        try:
            os.remove(file)
            logger.success(f"Deleted: {file}")
        except Exception as e:
            logger.error(f"Error deleting {file}: {e}")


def load_config(file_path):
    with open(file_path) as file:
        config = yaml.safe_load(file)
        if config:
            logger.success("Loaded YAML configuration")
    return config


def make_dir(script_path, output_path):
    if not os.path.isfile(script_path):
        logger.error(f"Error: Script not found: {script_path}")
        sys.exit(1)
    if not os.path.isdir(output_path):
        logger.info(f"Output path not found, so creating it {output_path}")
        os.makedirs(output_path)
    pass


def get_bin_path(build_type):
    base_dir = (
        get_workspace_path()
        / "benchmark"
        / "basic_performance"
        / "build"
        / "bw_latency_test"
        / f"{build_type}"
        / "build"
    )
    paths = {
        "release": os.path.join(base_dir, "cxl_perf_app_release/bin/cxl_perf_app"),
        "designtest": os.path.join(base_dir, "cxl_perf_app_designtest/cxl_perf_app_designtest"),
    }

    if build_type not in paths:
        logger.error("Error: Invalid build type")
        sys.exit(1)

    return paths[build_type]


def make_yaml_file(
    output_path,
    job_id,
    num_threads,
    lt_pattern_block_size,
    lt_pattern_access_size,
    lt_pattern_stride_size,
    delay,
    numa_node,
    core_socket,
    ldst_type,
    mem_alloc_type,
    latency_pattern,
    bandwidth_pattern,
    thread_buffer_size,
    pattern_iteration,
    bw_load_pattern_block_size,
    bw_store_pattern_block_size,
):
    config = {
        "job_id": job_id,
        "num_threads": num_threads,
        "lt_pattern_block_size": lt_pattern_block_size,
        "lt_pattern_access_size": lt_pattern_access_size,
        "lt_pattern_stride_size": lt_pattern_stride_size,
        "delay": delay,
        "numa_type": numa_node,
        "socket_type": core_socket,
        "loadstore_type": ldst_type,
        "mem_alloc_type": mem_alloc_type,
        "latency_pattern": latency_pattern,
        "bandwidth_pattern": bandwidth_pattern,
        "thread_buffer_size": thread_buffer_size,
        "pattern_iteration": pattern_iteration,
        "bw_load_pattern_block_size": bw_load_pattern_block_size,
        "bw_store_pattern_block_size": bw_store_pattern_block_size,
    }
    with open(output_path, "w") as file:
        yaml.dump(config, file)
    pass


def run_all(script_path, build_type, output_path):
    make_dir(script_path, output_path)
    bin_path = get_bin_path(build_type)
    cmd = f"sudo {bin_path} -f {script_path} -o {output_path}"
    run_as_sudo(cmd)
    pass


def get_thread_num_array(thread_num_type: int, config: dict, machine_type: str):
    if thread_num_type == 0:  # user defined
        return config["thread_num_array"]
    elif thread_num_type:  # Automatic thread detection with custom step size
        total_thread = get_cpu_number(machine_type) * get_thread_per_core(machine_type)
        return [i for i in range(1, total_thread, thread_num_type)]


def validate_buffer_size(buffer_size, numa_node, machine_type):
    total_thread = get_cpu_number(machine_type) * get_thread_per_core(machine_type)
    free_mem = get_free_memsize(numa_node)
    if buffer_size * total_thread > free_mem:
        logger.error(f"Error: Not enough memory for buffer size {buffer_size}MB, free memory: {free_mem}MB")
        return False
    return True


def search_valid_buffer_size(buffer_size, numa_node, machine_type):
    logger.info("Start to retrieve valid buffer size")
    free_mem = get_free_memsize(numa_node)
    thread_num = get_cpu_number(machine_type) * get_thread_per_core(machine_type)
    while buffer_size * thread_num > free_mem:
        buffer_size = buffer_size // 2
    logger.info(f"Valid buffer size: {buffer_size}MB")
    return buffer_size


def run_bw_latency_test(script_path, build_type, output_path, machine_type):
    config = load_config(script_path)
    thread_num_array = get_thread_num_array(config["thread_num_type"], config, machine_type)
    print(f"thread_num_array: {thread_num_array}")
    param_combinations = itertools.product(
        config["numa_node_array"],
        config["core_socket_array"],
        thread_num_array,
        config["latency_pattern_block_size_array_byte"],
        config["latency_pattern_access_size_array_byte"],
        config["latency_pattern_stride_size_array_byte"],
        config["delay_array"],
        config["loadstore_array"],
        config["mem_alloc_type_array"],
        config["latency_pattern_array"],
        config["bandwidth_pattern_array"],
        config["thread_buffer_size array_megabyte"],
        config["pattern_iteration_array"],
        config["bandwidth_load_pattern_block_size"],
        config["bandwidth_store_pattern_block_size"],
    )
    prepare_run(script_path, machine_type)
    for (
        numa_node,
        core_socket,
        num_threads,
        lt_pattern_block_size,
        lt_pattern_access_size,
        lt_pattern_stride_size,
        latency,
        ldst_type,
        mem_alloc_type,
        latency_pattern,
        bandwidth_pattern,
        thread_buffer_size,
        pattern_iteration,
        bw_load_pattern_block_size,
        bw_store_pattern_block_size,
    ) in param_combinations:
        if not validate_buffer_size(thread_buffer_size, numa_node, machine_type):
            thread_buffer_size = search_valid_buffer_size(thread_buffer_size, numa_node, machine_type)
        yaml_path = get_workspace_path() / "benchmark" / "basic_performance" / "scripts" / "batch" / "temp.yaml"
        make_yaml_file(
            yaml_path,
            config["job_id"],
            num_threads,
            lt_pattern_block_size,
            lt_pattern_access_size,
            lt_pattern_stride_size,
            latency,
            numa_node,
            core_socket,
            ldst_type,
            mem_alloc_type,
            latency_pattern,
            bandwidth_pattern,
            thread_buffer_size,
            pattern_iteration,
            bw_load_pattern_block_size,
            bw_store_pattern_block_size,
        )
        run_all(yaml_path, build_type, output_path)
        if build_type in ["designtest"]:
            break
    wrap_up_run(script_path, yaml_path, machine_type)
    pass


def run_batch(script_path, build_type, output_path, machine_type, task_id):
    if task_id in ["100", "101", "102"]:
        run_bw_latency_test(script_path, build_type, output_path, machine_type)
    elif task_id in ["200"]:
        cache_batch.run_cache_test(script_path, output_path)

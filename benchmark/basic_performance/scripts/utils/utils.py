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

import os
import platform
import re
import socket
from datetime import datetime

from invoke import run
from loguru import logger

from heimdall.utils.path import get_workspace_path


def find_file_with_prefix(task_number_prefix):
    directory = get_workspace_path() / "benchmark" / "basic_performance" / "scripts" / "batch"

    try:
        if not os.path.isdir(directory):
            logger.error(f"Error: Directory '{directory}' does not exist.")
            return []

        pattern = re.compile(rf"^{task_number_prefix}.*")

        matching_files = [f for f in os.listdir(directory) if pattern.match(f)]

        if len(matching_files) == 0:
            logger.error(f"No files found with prefix '{task_number_prefix}'")
            return []

        if len(matching_files) > 1:
            logger.error(f"Multiple files found with prefix '{task_number_prefix}'")
            return []

        return matching_files[0]

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return []


def check_task_continuous(task_file):
    while True:
        logger.info(f"Task file: {task_file}")
        yn = input("Start to run them [y/n]: ").strip().lower()
        if yn in ["y", "yes"]:
            return True
        elif yn in ["n", "no"]:
            logger.info("Exiting...")
            exit()
        else:
            logger.error("Invalid input")
            exit()


def get_task_id(task_prefix):
    current_time = datetime.now().strftime("%m-%d-%Y")
    result = run("git rev-parse --short HEAD", hide=True, warn=True)
    git_head = result.stdout.strip() if result.ok else "unknown"
    hostname = socket.gethostname()
    return f"basic-{current_time}-{task_prefix}-{git_head}-{hostname}"


def get_unique_task_id(base_directory, task_prefix):
    base_name = get_task_id(task_prefix)
    existing_files = [f for f in os.listdir(base_directory) if f.startswith(base_name)]
    max_index = -1
    for file in existing_files:
        parts = file[len(base_name) :].lstrip("-").split("-")
        if parts and parts[0].isdigit():
            max_index = max(max_index, int(parts[0]))

    return f"{base_directory}/{base_name}-{max_index + 1}"


def get_task_directory(task_prefix):
    base_dir = get_workspace_path() / "results" / "basic_performance" / f"{task_prefix}"
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)
    return get_unique_task_id(base_dir, task_prefix)


def get_architecture():
    arch = platform.machine().lower()
    logger.info(f"Architecture is {arch}")
    if arch in ["x86_64", "amd64"]:
        return "x86"
    elif arch in ["aarch64"]:
        return "arm"
    else:
        logger.error(f"unknown architecture: {arch}")
        exit(1)


def get_cpu_number(machine_type):
    if machine_type in ["x86"]:
        result = run(
            "lscpu | grep 'Core(s) per socket:' | awk '{print $4}'",
            hide=True,
            warn=True,
        )
    elif machine_type in ["arm"]:
        result = run(
            "lscpu | grep 'Core(s) per cluster:' | awk '{print $4}'",
            hide=True,
            warn=True,
        )
    else:
        logger.error(f"unknown machine type: {machine_type}")
        exit(1)

    if result.ok:
        logger.info(f"CPU number: {result.stdout.strip()}")
        return int(result.stdout.strip())
    else:
        logger.error(f"Failed to get CPU number: {result.stderr}")
        exit(1)


def get_thread_per_core(machine_type):
    if machine_type in ["x86"]:
        result = run(
            "lscpu | grep 'Thread(s) per core:' | awk '{print $4}'",
            hide=True,
            warn=True,
        )
    elif machine_type in ["arm"]:
        result = run(
            "lscpu | grep 'Thread(s) per core:' | awk '{print $4}'",
            hide=True,
            warn=True,
        )
    else:
        logger.error(f"unknown machine type: {machine_type}")
        exit(1)

    if result.ok:
        logger.info(f"Thread per core: {result.stdout.strip()}")
        return int(result.stdout.strip())
    else:
        logger.error(f"Failed to get Thread per core: {result.stderr}")
        exit(1)


def get_free_memsize(numa_node):
    result = run("numactl --hardware", hide=True, warn=True)

    if result.ok:
        output = result.stdout
        match = re.search(rf"node {numa_node} free:\s+(\d+) MB", output)
        if match:
            free_size_mb = int(match.group(1))
            logger.info(f"Free memory size: {free_size_mb}MB")
            return free_size_mb

    logger.error(f"Failed to get free memory size for NUMA node {numa_node}")
    exit(1)

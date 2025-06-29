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

import itertools
import os
import socket
import sys
import time

import yaml
from dotenv import load_dotenv
from invoke import run
from loguru import logger

import benchmark.basic_performance.scripts.utils.aslr as aslr
import benchmark.basic_performance.scripts.utils.batch as batchutils
import benchmark.basic_performance.scripts.utils.dvfs as dvfs
import benchmark.basic_performance.scripts.utils.prefetch as prefetch
import benchmark.basic_performance.scripts.utils.slack as slack
import benchmark.basic_performance.scripts.utils.smt as smt
from benchmark.basic_performance.scripts.utils.sudo import run_as_sudo
from heimdall.utils.path import get_workspace_path


def make_yaml_file(
    yaml_path,
    repeat,
    core_id,
    node_id,
    use_flush,
    access_order,
    dimm_start_addr_phys,
    dimm_test_size,
    stride_size,
    block_num,
    test_size,
):
    with open(yaml_path, "w") as f:
        yaml.dump(
            {
                "repeat": repeat,
                "core_id": core_id,
                "node_id": node_id,
                "use_flush": use_flush,
                "access_order": access_order,
                "dimm_start_addr_phys": dimm_start_addr_phys,
                "dimm_test_size": dimm_test_size,
                "stride_size": stride_size,
                "block_num": block_num,
                "test_size": test_size,
            },
            f,
        )
    pass


def get_bin_path():
    bin_path = (
        get_workspace_path()
        / "benchmark"
        / "basic_performance"
        / "build"
        / "cache_test"
        / "user_space"
        / "build"
        / "bin"
        / "cxl_perf_app_cache"
    )
    return bin_path


def run_test(script_path, output_path):
    batchutils.make_dir(script_path, output_path)
    bin_path = get_bin_path()
    cmd = f"{bin_path} -f {script_path} -o {output_path}"
    run_as_sudo(cmd)
    pass


def prepare_run(task_file):
    slack.slack_notice_beg(f"start to run {task_file}")
    smt.turn_off_smt()
    aslr.set_aslr("off")
    prefetch.set_prefetcher("off")
    dvfs.set_cpu_boost("performance")
    pass


def wrap_up_run(task_file):
    slack.slack_notice_end(f"end to run {task_file}")
    smt.turn_on_smt()
    aslr.set_aslr("on")
    prefetch.set_prefetcher("on")
    pass


def check_and_remove_module(module_name):
    result = run("lsmod", hide=True, warn=True)

    if any(line.startswith(module_name + " ") for line in result.stdout.splitlines()):
        logger.info(f"{module_name} module exists")
        run_as_sudo(f"rmmod {module_name}")
        logger.success(f"{module_name} module removed successfully")
    else:
        logger.info(f"{module_name} module not found")


def insert_module():
    logger.info("Inserting module")
    module_path = (
        get_workspace_path()
        / "benchmark"
        / "basic_performance"
        / "src"
        / "machine"
        / "x86"
        / "pointer_chasing"
        / "pointer_chasing.ko"
    )
    if not os.path.exists(module_path):
        logger.error(f"Module file {module_path} does not exist.")
        sys.exit(1)

    cmd = f"insmod {module_path}"
    check_and_remove_module("pointer_chasing")
    run_as_sudo(cmd)
    pass


def remove_kernel_file():
    # build_scripts_path = (
    #     get_workspace_path()
    #     / "benchmark"
    #     / "basic_performance"
    #     / "build"
    #     / "cache_test"
    #     / "module"
    #     / "build.py"
    # )
    # if not os.path.isfile(build_scripts_path):
    #     logger.error("Error: Build script not found")
    #     sys.exit(1)
    # run_as_sudo(f"python3 {build_scripts_path} clean")

    # TODO: This can be a direct call to that funciton, no need to use `sub_cmd`
    # run_heimdall_sub_cmd("basic-performance build cache-test module clean")

    from benchmark.basic_performance.build.cache_test.module import clean

    clean()


def load_global_env():
    host_name = socket.gethostname()
    path = get_workspace_path() / "benchmark" / "basic_performance" / "env_files" / f"{host_name}.env"
    if not os.path.isfile(path):
        logger.error(f"Error: {path} not found")
        raise Exception("Error please make machine env file first @ utils/env_files")
    load_dotenv(dotenv_path=path)
    logger.info(f"hostname: {host_name}")
    logger.info(f"dimm_phys_addr: {os.getenv('dimm_physical_start_addr')}")
    logger.info(f"dimm_test_size: {os.getenv('dimm_test_size')}")


def run_cache_test(script_path, output_path):
    config = batchutils.load_config(script_path)
    insert_module()
    load_global_env()
    dimm_phys_addr = os.getenv("dimm_physical_start_addr")
    dimm_test_size = os.getenv("dimm_test_size")
    param_combinations = itertools.product(
        config["repeat"],
        config["core_id"],
        config["node_id"],
        config["use_flush"],
        config["access_order"],
        config["stride_size_array"],
        config["block_num_array"],
        config["test_size_array"],
    )
    prepare_run(script_path)
    for (
        repeat,
        core_id,
        node_id,
        use_flush,
        access_order,
        stride_size,
        block_num,
        test_size,
    ) in param_combinations:
        if block_num * stride_size >= test_size:
            continue
        yaml_path = get_workspace_path() / "benchmark" / "basic_performance" / "scripts" / "batch" / "temp.yaml"
        make_yaml_file(
            yaml_path,
            repeat,
            core_id,
            node_id,
            use_flush,
            access_order,
            dimm_phys_addr,
            dimm_test_size,
            stride_size,
            block_num,
            test_size,
        )
        run_test(yaml_path, output_path)
        time.sleep(1)
    wrap_up_run(script_path)
    check_and_remove_module("pointer_chasing")
    remove_kernel_file()

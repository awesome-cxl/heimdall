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
import subprocess
import sys
import time

import benchmark.basic_performance.scripts.utils.aslr as aslr
import benchmark.basic_performance.scripts.utils.batch as batchutils
import benchmark.basic_performance.scripts.utils.dvfs as dvfs
import benchmark.basic_performance.scripts.utils.prefetch as prefetch
import benchmark.basic_performance.scripts.utils.slack as slack
import benchmark.basic_performance.scripts.utils.smt as smt
import yaml
from dotenv import load_dotenv


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
    bin_path = os.path.join(
        os.path.dirname(__file__),
        "./../../build/cache_test/user_space/build/bin/cxl_perf_app_cache",
    )
    return bin_path


def run(script_path, output_path):
    batchutils.make_dir(script_path, output_path)
    bin_path = get_bin_path()
    cmd = [bin_path, "-f", script_path, "-o", output_path]
    print("Command: ", cmd)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error: Test failed with error code {e.returncode}")
        sys.exit(1)
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
    result = subprocess.run(["lsmod"], capture_output=True, text=True)

    if any(line.startswith(module_name + " ") for line in result.stdout.splitlines()):
        print(f"{module_name} module exists")

        try:
            subprocess.run(["sudo", "rmmod", module_name], check=True)
            print(f"{module_name} module removed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to remove {module_name}: {e}")
    else:
        print(f"{module_name} module not found")


def insert_module():
    print("Inserting module")
    module_path = os.path.join(
        os.path.dirname(__file__),
        "./../../src/machine/x86/pointer_chasing/pointer_chasing.ko",
    )
    if not os.path.exists(module_path):
        print(f"Module file {module_path} does not exist.")
        sys.exit(1)

    cmd = ["sudo", "insmod", module_path]
    print("Command: ", cmd)
    check_and_remove_module("pointer_chasing")
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error: Test failed with error code {e.returncode}")
        sys.exit(1)
    pass


def remove_kernel_file():
    build_scripts_path = os.path.join(
        os.path.dirname(__file__), "../../build/cache_test/module/build.py"
    )
    if not os.path.isfile(build_scripts_path):
        print("Error: Build script not found")
        sys.exit(1)
    try:
        subprocess.check_call(["python3", build_scripts_path, "clean"])
    except subprocess.CalledProcessError as e:
        print(f"Error: Test failed with error code {e.returncode}")
        sys.exit(1)


def load_global_env():
    host_name = socket.gethostname()
    path = os.path.join(os.path.dirname(__file__), f"./env_files/{host_name}.env")
    if not os.path.isfile(path):
        print(f"Error: {path} not found")
        print("Error please make machine env file first @ utils/env_files")
        sys.exit(1)
    load_dotenv(dotenv_path=path)
    print(f"hostname: {host_name}")
    print(f"dimm_phys_addr: {os.getenv('dimm_physical_start_addr')}")
    print(f"dimm_test_size: {os.getenv('dimm_test_size')}")


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
        yaml_path = os.path.join(os.path.dirname(__file__), "../batch/temp.yaml")
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
        run(yaml_path, output_path)
        time.sleep(1)
    wrap_up_run(script_path)
    check_and_remove_module("pointer_chasing")
    remove_kernel_file()

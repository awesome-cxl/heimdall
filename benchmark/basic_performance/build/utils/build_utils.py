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

import multiprocessing
import os
from dotenv import load_dotenv
import socket
from loguru import logger
from heimdall.utils.path import chdir, get_workspace_path
from heimdall.utils.cmd import run
from pathlib import Path


def get_numa_node_num(machine_type):
    if machine_type in ["x86"]:
        result = run("lscpu | grep 'NUMA node(s):' | awk '{print $3}'", hide=True, warn=True)
    elif machine_type in ["arm"]:
        logger.error("ARM architecture does not support NUMA node")
        exit(1)
    else:
        logger.error(f"unknown machine type: {machine_type}")
        exit(1)

    if result.ok:
        logger.info(f"NUMA node number: {result.stdout.strip()}")
        return int(result.stdout.strip())
    else:
        logger.error(f"Failed to get NUMA node number: {result.stderr}")
        exit(1)

def get_socket_number(machine_type):
    if machine_type in ["x86"]:
        result = run("lscpu | grep 'Socket(s):' | awk '{print $2}'", hide=True, warn=True)
    elif machine_type in ["arm"]:
        logger.error("ARM architecture does not support Socket number")
        exit(1)
    else:
        logger.error(f"unknown machine type: {machine_type}")
        exit(1)
    if result.ok:
        logger.info(f"Socket number: {result.stdout.strip()}")
        return int(result.stdout.strip())
    else:
        logger.error(f"Failed to get Socket number: {result.stderr}")
        exit(1)


def get_cpu_number(machine_type) :
    if machine_type in ["x86"]:
        result = run("lscpu | grep 'Core(s) per socket:' | awk '{print $4}'", hide=True, warn=True)
    elif machine_type in ["arm"]:
        result = run("lscpu | grep 'Core(s) per cluster:' | awk '{print $4}'", hide=True, warn=True)
    else:
        logger.error(f"unknown machine type: {machine_type}")
        exit(1)

    if result.ok:
        logger.info(f"CPU number: {result.stdout.strip()}")
        return int(result.stdout.strip())
    else:
        logger.error(f"Failed to get CPU number: {result.stderr}")
        exit(1)

def load_global_env():
    host_name = os.getenv("HEIMDALL_HOSTNAME")
    if not host_name:
        host_name = socket.gethostname()
    path = (
        get_workspace_path()
        / "benchmark"
        / "basic_performance"
        / "env_files"
        / f"{host_name}.env"
    )
    if not os.path.isfile(path):
        logger.error(f"Error: {path} not found")
        raise Exception(f"Error: did not find an env file for the current machine, please create one at {path}")
    load_dotenv(dotenv_path=path)


def clean(build_dir: Path, sudo: bool = False):
    build_dir = build_dir.resolve()
    if os.path.exists(build_dir):
        run(f"rm -rf {build_dir}", sudo=True)


def make_build_dir(build_dir, sudo: bool = False):
    build_dir = build_dir.resolve()
    if not os.path.exists(build_dir):
        run(f"mkdir -p {build_dir}", sudo=True)


def get_threads_num():
    return min(16, multiprocessing.cpu_count())


def run_cmake(build_dir: Path, arch: str, sudo: bool = False):
    build_dir = build_dir.resolve()
    load_global_env()
    with chdir(build_dir):
        if arch in ["x86", "X86"]:
            machine_type = 1
        elif arch in ["arm", "ARM"]:
            machine_type = 2
        elif arch in ["mockup", "MOCKUP"]:
            machine_type = 3
        else:
            raise ValueError(f"Unknown machine type: {arch}")
        core_num_per_socket = get_cpu_number(arch)
        socket_num = get_socket_number(arch)
        print(f"machine_type: {machine_type}, core_num_per_socket: {core_num_per_socket}, socket_num: {socket_num}")
        run(
            " ".join(
                [
                    "cmake .. -DCMAKE_BUILD_TYPE=Release",
                    f"-DMACHINE_TYPE={machine_type}",
                    f"-DCORE_NUM_PER_SOCKET={core_num_per_socket}",
                    f"-DMAX_SOCKET_NUM={socket_num}"
                ]
            ),
            sudo=True,
            pty=True,
        )
        numbers = get_threads_num()
        run(f"cmake --build . -j{numbers}", sudo=True)


def run_build(build_dir: Path, arch, sudo=False):
    build_dir = build_dir.resolve()

    clean(build_dir, sudo=True)
    make_build_dir(build_dir, sudo=True)
    run_cmake(build_dir, arch, sudo=True)

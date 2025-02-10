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
import shutil
import argparse
from dotenv import load_dotenv
import socket
import sys
from invoke import run
from loguru import logger
from heimdall.utils.path import chdir


def load_global_env():
    host_name = socket.gethostname()
    path = os.path.join(os.path.dirname(__file__), f"../../env_files/{host_name}.env")
    if not os.path.isfile(path):
        logger.error(f"Error: {path} not found")
        logger.error("Error please make machine env file first @ utils/env_files")
        sys.exit(1)
    load_dotenv(dotenv_path=path)
    logger.info(f"core num: {os.getenv('core_num_per_socker')}")


def clean(build_dir):
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)


def make_build_dir(build_dir):
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)


def get_threads_num():
    return min(16, multiprocessing.cpu_count())


def run_cmake(build_dir, arch):
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
        run(
            " ".join(
                [
                    "cmake .. -DCMAKE_BUILD_TYPE=Release",
                    f"-DMACHINE_TYPE={machine_type}",
                    f"-DCORE_NUM_PER_SOCKET={os.getenv('core_num_per_socker')}",
                ]
            ),
            echo=True,
        )
        numbers = get_threads_num()
        run(f"cmake --build . -j{numbers}", echo=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Build script")
    parser.add_argument("-m", type=str, default="x86", help="Machine type ( x86, ARM)")
    args = parser.parse_args()
    return args


def run_build(build_dir, arch):
    clean(build_dir)
    make_build_dir(build_dir)
    run_cmake(build_dir, arch)

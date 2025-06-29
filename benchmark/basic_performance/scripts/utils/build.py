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

import sys

import typer
from loguru import logger

app = typer.Typer()


def build_bw_latency(machine_type, build_type):
    if build_type == "release" or build_type == "designtest":
        logger.info(f"Building {build_type} for {machine_type} machine")
    else:
        logger.error("Error: Invalid build type")
        sys.exit(1)

    if machine_type == "x86" or machine_type == "arm" or machine_type == "mockup":
        logger.info(f"Running build script for {machine_type} machine")
        from benchmark.basic_performance.build.bw_latency_test.release import build

        build(machine_type)
    else:
        logger.error("Error: Invalid machine type")
        sys.exit(1)


def build_kernel(build_type):
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
    # run_as_sudo(f"python3 {build_scripts_path} build")
    # logger.info(f"Building {build_type} for kernel")
    from benchmark.basic_performance.build.cache_test.module import build, clean

    clean()
    build()


def build_cache_user(build_type):
    # build_scripts_path = (
    #     get_workspace_path()
    #     / "benchmark"
    #     / "basic_performance"
    #     / "build"
    #     / "cache_test"
    #     / "user_space"
    #     / "build.py"
    # )
    # if not os.path.isfile(build_scripts_path):
    #     logger.error("Error: Build script not found")
    #     sys.exit(1)
    # logger.info(f"Building {build_type} for cache user")
    # run_as_sudo(f"python3 {build_scripts_path}")

    from benchmark.basic_performance.build.cache_test.user_space import build

    build()


def build_cache(build_type):
    logger.info("start build cache")
    build_kernel(build_type)
    build_cache_user(build_type)


def build(machine_type, build_type, task_id):
    if task_id in ["100", "101", "102"]:
        build_bw_latency(machine_type, build_type)
    elif task_id in ["200"]:
        build_cache(build_type)
    else:
        logger.error("Error: Invalid task id")
        sys.exit(1)

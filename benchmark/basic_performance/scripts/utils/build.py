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
import subprocess
import sys
import typer

app = typer.Typer()

def build_bw_latency(machine_type, build_type):

    if build_type == "release" or build_type == "designtest":
        print(f"Building {build_type} for {machine_type} machine")
        build_scripts_path = os.path.join(
            os.path.dirname(__file__),
            f"../../build/bw_latency_test/{build_type}/build.py",
        )
    else:
        print("Error: Invalid build type")
        sys.exit(1)

    if not os.path.isfile(build_scripts_path):
        print("Error: Build script not found")
        sys.exit(1)

    if machine_type == "x86" or machine_type == "arm" or machine_type == "mockup":
        try:
            print(f"Running build script for {machine_type} machine")
            subprocess.check_call(["python3", build_scripts_path, "-m", machine_type])
        except subprocess.CalledProcessError as e:
            print(f"Error: Build failed with error code {e.returncode}")
            sys.exit(1)
    else:
        print("Error: Invalid machine type")
        sys.exit(1)


def build_kernel(build_type):
    build_scripts_path = os.path.join(
        os.path.dirname(__file__), "../../build/cache_test/module/build.py"
    )
    if not os.path.isfile(build_scripts_path):
        print("Error: Build script not found")
        sys.exit(1)
    try:
        print(f"Building {build_type} for kernel")
        subprocess.check_call(["python3", build_scripts_path, "clean"])
        subprocess.check_call(["python3", build_scripts_path, "build"])
    except subprocess.CalledProcessError as e:
        print(f"Error: Build failed with error code {e.returncode}")
        sys.exit(1)


def build_cache_user(build_type):
    build_scripts_path = os.path.join(
        os.path.dirname(__file__), "../../build/cache_test/user_space/build.py"
    )
    if not os.path.isfile(build_scripts_path):
        print("Error: Build script not found")
        sys.exit(1)
    try:
        print(f"Building {build_type} for cache user")
        subprocess.check_call(["python3", build_scripts_path])
    except subprocess.CalledProcessError as e:
        print(f"Error: Build failed with error code {e.returncode}")
        sys.exit(1)


def build_cache(build_type):
    print("start build cache")
    build_kernel(build_type)
    build_cache_user(build_type)


def build(machine_type, build_type, task_id):
    if task_id in ["100", "101", "102"]:
        build_bw_latency(machine_type, build_type)
    elif task_id in ["200"]:
        build_cache(build_type)
    else:
        print("Error: Invalid task id")
        sys.exit(1)

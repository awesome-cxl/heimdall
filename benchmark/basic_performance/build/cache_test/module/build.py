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

# Define paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")  # CMake build directory
SRC_DIR = os.path.join(
    SCRIPT_DIR, "../../../src/machine/x86/pointer_chasing"
)  # Kernel module source directory


def run_command(command, cwd=None):
    try:
        subprocess.run(command, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {command}\n{e}")
        sys.exit(1)


def build_kernel_module():
    print("Configuring CMake...")
    os.makedirs(BUILD_DIR, exist_ok=True)
    run_command(f"cmake {SCRIPT_DIR}", cwd=BUILD_DIR)

    print("Building kernel module...")
    run_command("make build_kernel_module", cwd=BUILD_DIR)


def clean_kernel_module():
    print("Cleaning kernel module...")
    if not os.path.exists(BUILD_DIR):
        print("No build directory found. Nothing to clean.")
        return
    run_command("make clean_kernel_module", cwd=BUILD_DIR)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["build", "clean"]:
        print("Usage: python build_kernel_module.py <build|clean>")
        sys.exit(1)

    if sys.argv[1] == "build":
        build_kernel_module()
    elif sys.argv[1] == "clean":
        clean_kernel_module()

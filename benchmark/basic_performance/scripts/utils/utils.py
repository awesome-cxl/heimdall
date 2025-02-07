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
import re
import socket
import subprocess
from datetime import datetime
import platform


def find_file_with_prefix(task_number_prefix):
    directory = os.path.join(os.path.dirname(__file__), "../batch")
    print(f"directory: {directory}")
    try:
        if not os.path.isdir(directory):
            print(f"Error: Directory '{directory}' does not exist.")
            return []

        pattern = re.compile(rf"^{task_number_prefix}.*")

        matching_files = [f for f in os.listdir(directory) if pattern.match(f)]

        if len(matching_files) == 0:
            print(f"No files found with prefix '{task_number_prefix}'")
            return []

        if len(matching_files) > 1:
            print(f"Multiple files found with prefix '{task_number_prefix}'")
            return []

        return matching_files[0]

    except Exception as e:
        print(f"Error: {str(e)}")
        return []


def check_task_continuous(task_file):
    while True:
        print(f"Task file: {task_file}")
        yn = input("Start to run them [y/n]: ").strip().lower()
        if yn in ["y", "yes"]:
            return True
        elif yn in ["n", "no"]:
            print("Exiting...")
            exit()
        else:
            print("Invalid input")
            exit()


def get_task_id(task_prefix):
    current_time = datetime.now().strftime("%m-%d-%Y")
    try:
        git_head = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        git_head = "unknown"
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
    base_dir = os.path.join(os.path.dirname(__file__), "../../../../../results/basic_performance/{task_prefix}")
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)
    return get_unique_task_id(base_dir, task_prefix)

def get_architecture():
    arch = platform.machine().lower()
    print(f"Architecture is {arch}")
    if arch in ["x86_64", "amd64"]:
        return "x86"
    elif arch in ["aarch64"]:
        return "arm"
    else:
        print(f"unknown architecture: {arch}")
        exit(1)
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
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")


def setup_path():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    import utils.build_utils as build_utils

    return build_utils


if __name__ == "__main__":
    # Clean and create build directory
    build_utils = setup_path()
    build_utils.clean(BUILD_DIR)
    build_utils.make_build_dir(BUILD_DIR)

    # Ensure CMake is configured before building
    subprocess.run(["cmake", ".."], cwd=BUILD_DIR, check=True)

    # Get the number of threads
    numbers = build_utils.get_threads_num()

    # Build the project
    subprocess.run(["cmake", "--build", ".", f"-j{numbers}"], cwd=BUILD_DIR, check=True)

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

import glob
import os

from loguru import logger

from benchmark.basic_performance.scripts.utils.sudo import run_as_sudo


def set_cpu_boost(mode):
    if mode not in ["performance", "powersave"]:
        logger.error(f"Invalid mode: {mode}")
        return

    for file_path in glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"):
        logger.info(f"Set {mode} mode for {file_path}")
        cmd = f"echo {mode} | tee {file_path}"
        run_as_sudo(cmd)


def control_cpu_boost():
    if os.getenv("boost_cpu") == "True":
        set_cpu_boost("performance")
    else:
        set_cpu_boost("powersave")

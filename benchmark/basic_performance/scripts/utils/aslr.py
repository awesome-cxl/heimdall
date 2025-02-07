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

from loguru import logger

from benchmark.basic_performance.scripts.utils.sudo import run_as_sudo


def set_aslr(state):
    if state == "on":
        value = "2"
        logger.info("Turning ASLR on")
    elif state == "off":
        value = "0"
        logger.info("Turning ASLR off")
    else:
        logger.error(f"Invalid argument: {state}")
        logger.error("Usage: python script.py <on|off>")
        sys.exit(1)

    cmd = f"echo {value} | tee /proc/sys/kernel/randomize_va_space"
    run_as_sudo(cmd)

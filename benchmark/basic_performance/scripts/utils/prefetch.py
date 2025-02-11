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
import shutil
import sys

from invoke import run
from loguru import logger

from benchmark.basic_performance.scripts.utils.sudo import run_as_sudo


def check_msr_module():
    try:
        # Check if 'msr' module is loaded
        lsmod_output = run("lsmod", hide=True).stdout
        if "msr" not in lsmod_output:
            logger.error("ERROR: module 'msr' not inserted")
            sys.exit(1)

        # Check if 'rdmsr' command exists
        if not shutil.which("rdmsr"):
            logger.error("ERROR: command 'rdmsr' not found")
            sys.exit(1)

    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        sys.exit(1)


def set_prefetcher_intel(mode):
    if mode == "off":
        run_as_sudo("wrmsr -a 0x1a4 0x2f")
    elif mode == "on":
        run_as_sudo("wrmsr -a 0x1a4 0x0")
    elif mode == "show":
        run_as_sudo("rdmsr -a 0x1a4")
    else:
        logger.error(f"Invalid mode: {mode}")


def set_prefetcher_amd(mode):
    try:
        with open("/proc/cpuinfo", "r") as cpuinfo:
            cpuinfo_data = cpuinfo.read()

        if "cpu family" in cpuinfo_data and "25" in cpuinfo_data:
            if "model" in cpuinfo_data and ("17" in cpuinfo_data or "144" in cpuinfo_data):
                logger.info("Detected Zen4 CPU")
                if mode == "off":
                    run_as_sudo("wrmsr -a 0xc0011020 0x4400000000000")
                    run_as_sudo("wrmsr -a 0xc0011021 0x4000000000040")
                    run_as_sudo("wrmsr -a 0xc0011022 0x8680000401570000")
                    run_as_sudo("wrmsr -a 0xc001102b 0x2040cc10")
                    logger.success("MSR register values for Zen4 applied: OFF")
                elif mode == "on":
                    run_as_sudo("wrmsr -a 0xc0011020 0x4400200000000")
                    run_as_sudo("wrmsr -a 0xc0011021 0x4000000000040")
                    run_as_sudo("wrmsr -a 0xc0011022 0x8680000401500000")
                    run_as_sudo("wrmsr -a 0xc001102b 0x2040cc15")
                    logger.success("MSR register values for Zen4 applied: ON")
                elif mode == "show":
                    run_as_sudo("rdmsr -a 0xc0011020")
                    run_as_sudo("rdmsr -a 0xc0011021")
                    run_as_sudo("rdmsr -a 0xc0011022")
                    run_as_sudo("rdmsr -a 0xc001102b")
                else:
                    logger.error(f"Invalid mode: {mode}")
            else:
                logger.info("Detected Zen3 CPU")
                if mode == "off":
                    run_as_sudo("wrmsr -a 0xc0011020 0x4480000000000")
                    run_as_sudo("wrmsr -a 0xc0011021 0x1c000200000040")
                    run_as_sudo("wrmsr -a 0xc0011022 0xc000000401570000")
                    run_as_sudo("wrmsr -a 0xc001102b 0x2000cc10")
                    logger.success("MSR register values for Zen3 applied: OFF")
                elif mode == "on":
                    run_as_sudo("wrmsr -a 0xc0011020 0x4480000000000")
                    run_as_sudo("wrmsr -a 0xc0011021 0x2000000c0")
                    run_as_sudo("wrmsr -a 0xc0011022 0xc000000401500000")
                    run_as_sudo("wrmsr -a 0xc001102b 0x2000cc15")
                    logger.success("MSR register values for Zen3 applied: ON")
                elif mode == "show":
                    run_as_sudo("rdmsr -a 0xc0011020")
                    run_as_sudo("rdmsr -a 0xc0011021")
                    run_as_sudo("rdmsr -a 0xc0011022")
                    run_as_sudo("rdmsr -a 0xc001102b")
                else:
                    logger.error(f"Invalid mode: {mode}")
        else:
            logger.info("Detected Zen1/Zen2 CPU")
            if mode == "off":
                run_as_sudo("wrmsr -a 0xc0011020 0")
                run_as_sudo("wrmsr -a 0xc0011021 0x40")
                run_as_sudo("wrmsr -a 0xc0011022 0x1510000")
                run_as_sudo("wrmsr -a 0xc001102b 0x2000cc16")
                logger.success("MSR register values for Zen1/Zen2 applied: OFF")
            else:
                logger.error(
                    "ERROR: The script does not handle Zen1/2 msr register recovery"
                )

    except FileNotFoundError:
        logger.error("ERROR: '/proc/cpuinfo' not found")
        sys.exit(1)


def set_prefetcher(mode):
    check_msr_module()
    try:
        with open("/proc/cpuinfo", "r") as cpuinfo:
            cpuinfo_data = cpuinfo.read()

        if "AMD Ryzen" in cpuinfo_data or "AMD EPYC" in cpuinfo_data:
            set_prefetcher_amd(mode)
        else:
            set_prefetcher_intel(mode)
    except FileNotFoundError:
        logger.error("ERROR: '/proc/cpuinfo' not found")
        sys.exit(1)


def control_prefetch():
    if os.getenv("disable_prefetch") == "True":
        logger.info("Disable prefetch")
        set_prefetcher("off")
    else:
        logger.info("Enable prefetch")
        set_prefetcher("on")

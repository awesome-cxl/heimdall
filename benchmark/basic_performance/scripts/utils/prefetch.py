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
import subprocess
import sys


def check_msr_module():
    try:
        # Check if 'msr' module is loaded
        lsmod_output = subprocess.check_output(["lsmod"]).decode()
        if "msr" not in lsmod_output:
            print("ERROR: module 'msr' not inserted")
            sys.exit(1)

        # Check if 'rdmsr' command exists
        if not shutil.which("rdmsr"):
            print("ERROR: command 'rdmsr' not found")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)


def set_prefetcher_intel(mode):
    if mode == "off":
        os.system("wrmsr -a 0x1a4 0x2f")
    elif mode == "on":
        os.system("wrmsr -a 0x1a4 0x0")
    elif mode == "show":
        os.system("rdmsr -a 0x1a4")
    else:
        print(f"Invalid mode: {mode}")


def set_prefetcher_amd(mode):
    try:
        with open("/proc/cpuinfo", "r") as cpuinfo:
            cpuinfo_data = cpuinfo.read()

        if "cpu family" in cpuinfo_data and "25" in cpuinfo_data:
            if "model" in cpuinfo_data and "17" in cpuinfo_data:
                print("Detected Zen4 CPU")
                if mode == "off":
                    os.system("wrmsr -a 0xc0011020 0x4400000000000")
                    os.system("wrmsr -a 0xc0011021 0x4000000000040")
                    os.system("wrmsr -a 0xc0011022 0x8680000401570000")
                    os.system("wrmsr -a 0xc001102b 0x2040cc10")
                    print("MSR register values for Zen4 applied: OFF")
                elif mode == "on":
                    os.system("wrmsr -a 0xc0011020 0x4400200000000")
                    os.system("wrmsr -a 0xc0011021 0x4000000000040")
                    os.system("wrmsr -a 0xc0011022 0x8680000401500000")
                    os.system("wrmsr -a 0xc001102b 0x2040cc15")
                    print("MSR register values for Zen4 applied: ON")
                elif mode == "show":
                    os.system("rdmsr -a 0xc0011020")
                    os.system("rdmsr -a 0xc0011021")
                    os.system("rdmsr -a 0xc0011022")
                    os.system("rdmsr -a 0xc001102b")
                else:
                    print(f"Invalid mode: {mode}")
            else:
                print("Detected Zen3 CPU")
                if mode == "off":
                    os.system("wrmsr -a 0xc0011020 0x4480000000000")
                    os.system("wrmsr -a 0xc0011021 0x1c000200000040")
                    os.system("wrmsr -a 0xc0011022 0xc000000401570000")
                    os.system("wrmsr -a 0xc001102b 0x2000cc10")
                    print("MSR register values for Zen3 applied: OFF")
                elif mode == "on":
                    os.system("wrmsr -a 0xc0011020 0x4480000000000")
                    os.system("wrmsr -a 0xc0011021 0x2000000c0")
                    os.system("wrmsr -a 0xc0011022 0xc000000401500000")
                    os.system("wrmsr -a 0xc001102b 0x2000cc15")
                    print("MSR register values for Zen3 applied: ON")
                elif mode == "show":
                    os.system("rdmsr -a 0xc0011020")
                    os.system("rdmsr -a 0xc0011021")
                    os.system("rdmsr -a 0xc0011022")
                    os.system("rdmsr -a 0xc001102b")
                else:
                    print(f"Invalid mode: {mode}")
        else:
            print("Detected Zen1/Zen2 CPU")
            if mode == "off":
                os.system("wrmsr -a 0xc0011020 0")
                os.system("wrmsr -a 0xc0011021 0x40")
                os.system("wrmsr -a 0xc0011022 0x1510000")
                os.system("wrmsr -a 0xc001102b 0x2000cc16")
                print("MSR register values for Zen1/Zen2 applied: OFF")
            else:
                print("ERROR: The script does not handle Zen1/2 msr register recovery")

    except FileNotFoundError:
        print("ERROR: '/proc/cpuinfo' not found")
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
        print("ERROR: '/proc/cpuinfo' not found")
        sys.exit(1)


def control_prefetch():
    if os.getenv("disable_prefetch") == "True":
        print("prefetch off")
        set_prefetcher("off")
    else:
        print("prefetch on")
        set_prefetcher("on")

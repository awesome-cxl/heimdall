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


def turn_off_smt():
    smt_control_path = "/sys/devices/system/cpu/smt/control"

    try:
        print("Turning off SMT")
        with open(smt_control_path, "w") as file:
            file.write("off\n")
    except FileNotFoundError:
        print(f"Error: The file '{smt_control_path}' does not exist.")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied when accessing '{smt_control_path}'.")
        print("Try running the script as root or using sudo.")
        sys.exit(1)


def turn_on_smt():
    smt_control_path = "/sys/devices/system/cpu/smt/control"

    try:
        print("Turning on SMT")
        with open(smt_control_path, "w") as file:
            file.write("on\n")
    except FileNotFoundError:
        print(f"Error: The file '{smt_control_path}' does not exist.")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied when accessing '{smt_control_path}'.")
        print("Try running the script as root or using sudo.")
        sys.exit(1)

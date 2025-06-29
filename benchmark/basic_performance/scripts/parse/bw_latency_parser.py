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

import csv
import os
import re
from collections import defaultdict

from loguru import logger


def parse_result_logs(base_dir):
    parsed_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for root, _, files in os.walk(base_dir):
        if "result.log" in files:
            log_path = os.path.join(root, "result.log")
            with open(log_path) as f:
                content = f.read()

                # Test 정보 추출 (정규식 수정)
                test_info = re.search(
                    r"Test Information:\n"
                    r"Buffer Size: (\d+MiB)\n"
                    r"Number of Threads: (\d+)\n"
                    r"Job Id: (\d+)\n"
                    r"Access Type: (\w+)\n"
                    r"LoadStore Type: (\w+)\n"
                    r"Block Size: (\d+) bytes\n"
                    r"Mem alloc Type: (\w+)\n"
                    r"Latency Pattern: (\w+)\n"
                    r"Bandwidth Pattern: (\w+)\n",
                    content,
                )

                # Bandwidth 및 Latency 추출
                total_bandwidth = re.search(r"Total Bandwidth : ([\d.]+) MiB/s", content)
                measured_latency = re.search(r"Measured Latency : (\d+) ns", content)

                if test_info and total_bandwidth and measured_latency:
                    (
                        size,
                        threads,
                        job_id,
                        access_type,
                        loadstore_type,
                        block_size,
                        mem_alloc_type,
                        latency_pattern,
                        bw_pattern,
                    ) = test_info.groups()

                    parsed_data[access_type][latency_pattern][bw_pattern].append(
                        {
                            "Size": size,
                            "Threads": int(threads),
                            "Job Id": int(job_id),
                            "LoadStore Type": loadstore_type,
                            "Block Size (bytes)": int(block_size),
                            "Mem alloc Type": mem_alloc_type,
                            "Total Bandwidth (MiB/s)": float(total_bandwidth.group(1)),
                            "Measured Latency (ns)": int(measured_latency.group(1)),
                        }
                    )
                else:
                    logger.error(f"Skipping log file due to missing data: {log_path}")

    for access_type in parsed_data:
        for latency_pattern in parsed_data[access_type]:
            for bw_pattern in parsed_data[access_type][latency_pattern]:
                parsed_data[access_type][latency_pattern][bw_pattern] = sorted(
                    parsed_data[access_type][latency_pattern][bw_pattern],
                    key=lambda x: x["Threads"],
                )

    return parsed_data


def save_results_to_csv(data, output_file):
    with open(output_file, "w", newline="") as f:
        fieldnames = [
            "Device Type",
            "Access Type",
            "LoadStore Type",
            "Threads",
            "Block Size (bytes)",
            "Total Bandwidth (MiB/s)",
            "Measured Latency (ns)",
            "Latency Pattern",
            "Bandwidth Pattern",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for access_type, latency_patterns in data.items():
            for latency_pattern, bandwidth_patterns in latency_patterns.items():
                for bw_pattern, tests in bandwidth_patterns.items():
                    for test in tests:
                        row = {
                            "Access Type": access_type,
                            "Latency Pattern": latency_pattern,
                            "Bandwidth Pattern": bw_pattern,
                            "LoadStore Type": test["LoadStore Type"],
                            "Threads": test["Threads"],
                            "Block Size (bytes)": test["Block Size (bytes)"],
                            "Total Bandwidth (MiB/s)": test["Total Bandwidth (MiB/s)"],
                            "Measured Latency (ns)": test["Measured Latency (ns)"],
                        }
                        writer.writerow(row)
    logger.info(f"The result is saved in {output_file}")


def parse_bw_latency(base_dir):
    save_results_to_csv(parse_result_logs(base_dir), os.path.join(base_dir, "parsed_result_logs.csv"))


if __name__ == "__main__":
    base_directory = input("Type the base directory path: ")
    result_data = parse_result_logs(base_directory)

    output_file = os.path.join(base_directory, "parsed_result_logs.csv")
    save_results_to_csv(result_data, output_file)

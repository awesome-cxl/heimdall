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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger


# Function to read log data from a file
def read_log_file(file_path):
    with open(file_path) as file:
        return file.read()


def parse_pattern(base_dir):
    test_index = []
    block_result = []
    stride_result = []
    store_latency_cycle_list = []
    store_latency_ns_list = []
    load_latency_cycle_list = []
    load_latency_ns_list = []

    index = 0
    for root, _, files in os.walk(base_dir):
        if "result.log" in files:
            log_path = os.path.join(root, "result.log")
            with open(log_path) as f:
                content = f.read()
                test_info = re.search(
                    r"==========Test No.==========\n"
                    r"Number of block: (\d+)\n"
                    r"Stride Size: (\d+)\n"
                    r"Average store time:\s+(\d+)\s+cycles,\s+([\d\.]+)\s+ns\n"
                    r"Average load time:\s+(\d+)\s+cycles,\s+([\d\.]+)\s+ns",
                    content,
                )
                if test_info:
                    (
                        block_num,
                        stride_size,
                        store_lat_cycle,
                        store_lat_ns,
                        load_lat_cycle,
                        load_lat_ns,
                    ) = test_info.groups()

                    logger.info(
                        ", ".join(
                            [
                                f"Block Num: {block_num}",
                                f"Stride Size: {stride_size}",
                                f"Store Latency Cycle: {store_lat_cycle}",
                                f"Store Latency ns: {store_lat_ns}",
                                f"Load Latency Cycle: {load_lat_cycle}",
                                f"Load Latency ns: {load_lat_ns}",
                            ]
                        )
                    )

                    test_index.append(index)
                    block_result.append(int(block_num))
                    stride_result.append(int(stride_size))
                    store_latency_cycle_list.append(int(store_lat_cycle))
                    store_latency_ns_list.append(float(store_lat_ns))
                    load_latency_cycle_list.append(int(load_lat_cycle))
                    load_latency_ns_list.append(float(load_lat_ns))
                    index += 1

    return (
        test_index,
        block_result,
        stride_result,
        store_latency_cycle_list,
        store_latency_ns_list,
        load_latency_cycle_list,
        load_latency_ns_list,
    )


def parse_results(log_file_path):
    # Read the log data from the file
    (
        test_index,
        block_num,
        stride_size,
        store_latency_cycle,
        store_latency_ns,
        load_latency_cycle,
        load_latency_ns,
    ) = parse_pattern(log_file_path)

    # Initialize an empty list to store the parsed data
    data = []

    # Regex patterns to capture relevant information
    # test_pattern = r"==========Test No\.(\d+)=========="
    # block_pattern = r"Number of block: (\d+)"
    # stride_pattern = r"Stride Size: (\d+)"
    # store_pattern = r"Average store time:\s+(\d+)\s+cycles,\s+([\d\.]+)\s+ns"
    # load_pattern = r"Average load time:\s+(\d+)\s+cycles,\s+([\d\.]+)\s+ns"

    # Parse the log data
    # test_index = re.findall(test_pattern, log_data)
    # block_num = re.findall(block_pattern, log_data)
    # stride_size = re.findall(stride_pattern, log_data)
    # store_results = re.findall(store_pattern, log_data)
    # load_results = re.findall(load_pattern, log_data)

    # store_latency_cycle = []
    # store_latency_ns = []
    # for store_result in store_results:
    #    store_latency_cycle.append(store_result[0])
    #    store_latency_ns.append(store_result[1])

    # load_latency_cycle = []
    # load_latency_ns = []
    # for load_result in load_results:
    #    load_latency_cycle.append(load_result[0])
    #    load_latency_ns.append(load_result[1])

    # Store the parsed data in a list
    for i in range(len(test_index)):
        data.append(
            {
                "test_index": int(test_index[i]),
                "block_num": int(block_num[i]),
                "stride_size": int(stride_size[i]),
                "store_latency_cycle": int(store_latency_cycle[i]),
                "load_latency_cycle": int(load_latency_cycle[i]),
                "store_latency_ns": int(store_latency_ns[i]),
                "load_latency_ns": int(load_latency_ns[i]),
            }
        )

    # Create a DataFrame
    df = pd.DataFrame(data)
    return df


def format_label(value):
    if value >= 2**20:
        return f"{int(value / 2**20)}M"
    elif value >= 2**10:
        return f"{int(value / 2**10)}K"
    else:
        return str(value)


def plot_heatmap(df, access_op, base_dir):
    if access_op == "load":
        pivot_table_value = "load_latency_ns"
    elif access_op == "store":
        pivot_table_value = "store_latency_ns"
    else:
        raise ValueError("Invalid access operation. Use 'load' or 'store'.")

    pivot_table = df.pivot_table(
        index="block_num",
        columns="stride_size",
        values=pivot_table_value,
        aggfunc="mean",
    )

    y_ticks = [2**i for i in range(0, 21)]
    x_ticks = [2**i for i in range(6, 27)]

    pivot_table = pivot_table.reindex(index=y_ticks, columns=x_ticks)
    pivot_table = pivot_table.iloc[::-1]

    plt.figure(figsize=(10, 10))
    ax = sns.heatmap(pivot_table, annot=False, cmap="plasma")

    ax.set_xticks(np.arange(len(x_ticks)))
    ax.set_xticklabels([format_label(tick) for tick in x_ticks])
    ax.set_yticks(np.arange(len(y_ticks)))
    ax.set_yticklabels([format_label(tick) for tick in reversed(y_ticks)])

    plt.title(f"heatmap_{access_op}")
    plt.xlabel("Stride Size (Byte)")
    plt.ylabel("Number of Blocks")
    plt.savefig(f"{base_dir}/heatmap_{access_op}.pdf")
    plt.close()


def parse_and_plot(base_dir):
    results_df = parse_results(base_dir)
    results_df.to_csv(f"{base_dir}/results.csv", index=False)
    plot_heatmap(results_df, "load", base_dir)
    plot_heatmap(results_df, "store", base_dir)

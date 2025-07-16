#
# MIT License
#
# Copyright (c) 2025 Jangseon Park, Luyi Li
# Affiliation: University of California San Diego CSE
# Email: jap036@ucsd.edu, lul@014@ucsd.edu
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
    with open(file_path, "r") as file:
        return file.read()


def parse_pattern(base_dir):
    test_index = []
    block_result = []
    stride_result = []
    store_latency_cycle_list = []
    store_latency_ns_list = []
    load_latency_cycle_list = []
    load_latency_ns_list = []
    access_order_list = []
    snc_mode_list = []
    core_id_list = []
    node_id_list = []
    ldst_type_list = []

    index = 0
    for root, _, files in os.walk(base_dir):
        if "result.log" in files:
            log_path = os.path.join(root, "result.log")
            with open(log_path, "r") as f:
                content = f.read()
                test_info = re.search(
                    r"=============== Test Information ===============.*?"
                    r"Number of Block:\s+(\d+).*?"
                    r"Stride Size:\s+(\d+).*?"
                    r"SNC Mode:\s+(\d+).*?"
                    r"Core ID:\s+(\d+).*?"
                    r"Node ID:\s+(\d+).*?"
                    r"Access Order:\s+(\w+).*?"
                    r"Load/Store Type:\s+(\w+).*?"
                    r"=============== Test Results ===============.*?"
                    r"Average Store Latency:\s+(\d+)\s+cycles,\s+([\d.]+)\s+ns.*?"
                    r"Average Load Latency:\s+(\d+)\s+cycles,\s+([\d.]+)\s+ns",
                    content,
                    re.DOTALL  # Use DOTALL instead of MULTILINE to match across lines
                )
                if test_info:
                    (
                        block_num,
                        stride_size,
                        snc_mode,
                        core_id,
                        node_id,
                        access_order,
                        ldst_type,
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
                                f"SNC Mode: {snc_mode}",
                                f"Core ID: {core_id}",
                                f"Node ID: {node_id}",
                                f"Access Order: {access_order}",
                                f"Load/Store Type: {ldst_type}",
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
                    snc_mode_list.append(int(snc_mode))
                    core_id_list.append(int(core_id))
                    node_id_list.append(int(node_id))
                    access_order_list.append(access_order)
                    ldst_type_list.append(ldst_type)
                    store_latency_cycle_list.append(int(store_lat_cycle))
                    store_latency_ns_list.append(float(store_lat_ns))
                    load_latency_cycle_list.append(int(load_lat_cycle))
                    load_latency_ns_list.append(float(load_lat_ns))
                    index += 1

    return (
        test_index,
        block_result,
        stride_result,
        snc_mode_list,
        core_id_list,
        node_id_list,
        access_order_list,
        ldst_type_list,
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
        snc_mode,
        core_id,
        node_id,
        access_order,
        ldst_type,
        store_latency_cycle,
        store_latency_ns,
        load_latency_cycle,
        load_latency_ns,
    ) = parse_pattern(log_file_path)

    # Initialize an empty list to store the parsed data
    data = []
    # Store the parsed data in a list
    for i in range(len(test_index)):
        data.append(
            {
                "test_index": int(test_index[i]),
                "block_num": int(block_num[i]),
                "stride_size": int(stride_size[i]),
                "snc_mode": int(snc_mode[i]),
                "core_id": int(core_id[i]),
                "node_id": int(node_id[i]),
                "access_order": access_order[i],
                "ldst_type": ldst_type[i],
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
        return f"{int(value / 2 ** 20)}M"
    elif value >= 2**10:
        return f"{int(value / 2 ** 10)}K"
    else:
        return str(value)


def plot_heatmap(base_dir, df, access_op, snc_mode, core_id, node_id, access_order, ldst_type):
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
    ax = sns.heatmap(pivot_table, annot=False, cmap="plasma", vmin=0, vmax=800)

    ax.set_xticks(np.arange(len(x_ticks)))
    ax.set_xticklabels([format_label(tick) for tick in x_ticks])
    ax.set_yticks(np.arange(len(y_ticks)))
    ax.set_yticklabels([format_label(tick) for tick in reversed(y_ticks)])

    # plt.title(f"heatmap_{access_op}")
    plt.xlabel("Stride Size (Byte)")
    plt.ylabel("Number of Blocks")
    plt.savefig(f"{base_dir}/heatmap_{access_op}_snc{snc_mode}_core{core_id}_node{node_id}_{access_order}_{ldst_type}.pdf")
    plt.close()


def parse_plot_heatmap(base_dir):
    results_df = parse_results(base_dir)
    results_df.to_csv(f"{base_dir}/results.csv", index=False)
    snc_modes = results_df['snc_mode'].unique()
    core_ids = results_df['core_id'].unique()
    node_ids = results_df['node_id'].unique()
    access_orders = results_df['access_order'].unique()
    ldst_types = results_df['ldst_type'].unique()
    for snc_mode in snc_modes:
        for core_id in core_ids:
            for node_id in node_ids:
                for access_order in access_orders:
                    for ldst_type in ldst_types:
                        filtered_df = results_df[
                            (results_df["snc_mode"] == snc_mode)
                            & (results_df["core_id"] == core_id)
                            & (results_df["node_id"] == node_id)
                            & (results_df["access_order"] == access_order)
                            & (results_df["ldst_type"] == ldst_type)
                        ]
                        if not filtered_df.empty:
                            plot_heatmap(base_dir, filtered_df, "load", snc_mode, core_id, node_id, access_order, ldst_type)
                            plot_heatmap(base_dir, filtered_df, "store", snc_mode, core_id, node_id, access_order, ldst_type)


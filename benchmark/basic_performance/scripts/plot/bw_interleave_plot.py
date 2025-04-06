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

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger


def plot_weight_vs_bandwidth_and_save(df, output_file, title_prefix):
    grouped = df.groupby(["Access Type"])
    plt.figure(figsize=(10, 6))
    for (access_type), group in grouped[0:1]:
        plt.bar(
            group["NUMA Weight"],
            group["Total Bandwidth (MiB/s)"] / 1024,  # Convert to GB/s
            label=f"{access_type}",
        )
    plt.title(f"{title_prefix}: Threads vs Total Bandwidth")
    plt.xlabel("NUMA Weight Ratio")
    plt.ylabel("Total Bandwidth (GiB/s)")
    plt.grid(True)
    plt.legend()
    plt.savefig(output_file)
    plt.close()


def plot_weight_vs_latency_and_save(df, output_file, title_prefix):
    grouped = df.groupby(["Access Type"])
    plt.figure(figsize=(10, 6))
    for (access_type), group in grouped[0:1]:
        plt.bar(
            group["NUMA Weight"],
            group["Measured Latency (ns)"],
            label=f"{access_type}",
        )
    plt.title(f"{title_prefix}: Threads vs Measured Latency")
    plt.xlabel("NUMA Weight Ratio")
    plt.ylabel("Measured Latency (ns)")
    plt.grid(True)
    plt.legend()
    plt.savefig(output_file)
    plt.close()


def plot_bw_weighted_numa(base_dir):
    file_path = base_dir + "/parsed_result_logs.csv"
    data = pd.read_csv(file_path)

    output_dir = os.path.dirname(file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    load_data = data[data["LoadStore Type"] == "LOAD"]
    store_data = data[data["LoadStore Type"] == "STORE"]

    load_output_files = {
        "numa_weight_vs_bandwidth": os.path.join(
            output_dir, "load_numa_weight_vs_bandwidth_plot.pdf"
        ),
        "numa_weight_vs_latency": os.path.join(
            output_dir, "load_numa_weight_vs_latency_plot.pdf"
        ),
    }

    store_output_files = {
        "numa_weight_vs_bandwidth": os.path.join(
            output_dir, "store_numa_weight_vs_bandwidth_plot.pdf"
        ),
        "numa_weight_vs_latency": os.path.join(
            output_dir, "store_numa_weight_vs_latency_plot.pdf"
        ),
    }

    if load_data.empty:
        logger.info("No LOAD data found.")
    else:
        plot_weight_vs_bandwidth_and_save(
            load_data, load_output_files["numa_weight_vs_bandwidth"], "LOAD"
        )
        plot_weight_vs_latency_and_save(
            load_data, load_output_files["numa_weight_vs_latency"], "LOAD"
        )

    if store_data.empty:
        logger.info("No STORE data found.")
    else:
        plot_weight_vs_bandwidth_and_save(
            store_data, store_output_files["numa_weight_vs_bandwidth"], "STORE"
        )
        plot_weight_vs_latency_and_save(
            store_data, store_output_files["numa_weight_vs_latency"], "STORE"
        )

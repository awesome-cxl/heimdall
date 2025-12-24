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

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger


# Define plotting functions
def plot_bandwidth_vs_latency_and_save(df, output_file, title_prefix):
    grouped = df.groupby(["Access Type"])
    plt.figure(figsize=(10, 6))
    for (access_type), group in grouped:
        total_bandwidth_gb = group["Total Bandwidth (MiB/s)"] / 1024
        plt.plot(
            total_bandwidth_gb,
            group["Measured Latency (ns)"],
            marker="o",
            label=f"{access_type}",
        )
    plt.title(f"{title_prefix}: Measured Latency vs Total Bandwidth")
    plt.xlabel("Total Bandwidth (GiB/s)")
    plt.ylabel("Measured Latency (ns)")
    plt.ylim(0, 2500)
    plt.legend()
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()


def plot_threads_vs_bandwidth_and_save(df, output_file, title_prefix):
    grouped = df.groupby(["Access Type"])
    plt.figure(figsize=(10, 6))
    for (access_type), group in grouped:
        plt.plot(
            group["Threads"],
            group["Total Bandwidth (MiB/s)"] / 1024,  # Convert to GB/s
            marker="o",
            label=f"{access_type}",
        )
    plt.title(f"{title_prefix}: Threads vs Total Bandwidth")
    plt.xlabel("Threads")
    plt.ylabel("Total Bandwidth (GiB/s)")
    plt.grid(True)
    plt.legend()
    plt.savefig(output_file)
    plt.close()


def plot_threads_vs_latency_and_save(df, output_file, title_prefix):
    grouped = df.groupby(["Access Type"])
    plt.figure(figsize=(10, 6))
    for (access_type), group in grouped:
        plt.plot(
            group["Threads"],
            group["Measured Latency (ns)"],
            marker="o",
            label=f"{access_type}",
        )
    plt.title(f"{title_prefix}: Threads vs Measured Latency")
    plt.xlabel("Threads")
    plt.ylabel("Measured Latency (ns)")
    plt.grid(True)
    plt.legend()
    plt.savefig(output_file)
    plt.close()

def plot_threads_vs_bw_latency_and_save(df, output_file, title_prefix):
    # Combined plot:
    # - X axis: Number of Threads
    # - Left Y axis (blue): Bandwidth
    # - Right Y axis (red): Latency
    grouped = df.groupby(["Access Type"])
    access_types = list(grouped.groups.keys())

    fig, ax_bw = plt.subplots(figsize=(10, 6))
    ax_lat = ax_bw.twinx()

    bw_handles = []
    lat_handles = []
    legend_labels = []

    single_access_type = len(access_types) == 1

    for (access_type), group in grouped:
        group_sorted = group.sort_values("Threads")
        threads = group_sorted["Threads"]
        bandwidth = group_sorted["Total Bandwidth (MiB/s)"] / 1024  # GiB/s
        latency = group_sorted["Measured Latency (ns)"]

        if single_access_type:
            (bw_line,) = ax_bw.plot(
                threads,
                bandwidth,
                marker="o",
                linestyle="-",
                linewidth=3,
                color="tab:blue",
            )
            (lat_line,) = ax_lat.plot(
                threads,
                latency,
                marker="x",
                linestyle="--",
                linewidth=3,
                color="tab:red",
            )
            bw_handles.append(bw_line)
            lat_handles.append(lat_line)
            legend_labels.extend(["Bandwidth", "Latency"])
        else:
            # Keep a consistent color per access_type across both axes.
            (bw_line,) = ax_bw.plot(
                threads,
                bandwidth,
                marker="o",
                linestyle="-",
                linewidth=2,
            )
            color = bw_line.get_color()
            (lat_line,) = ax_lat.plot(
                threads,
                latency,
                marker="x",
                linestyle="--",
                linewidth=2,
                color=color,
            )

            bw_handles.append(bw_line)
            lat_handles.append(lat_line)
            legend_labels.append(f"{access_type} BW")
            legend_labels.append(f"{access_type} Lat")

    ax_bw.set_title(f"{title_prefix}: Threads vs Bandwidth & Latency")
    ax_bw.set_xlabel("Number of Threads")
    ax_bw.set_ylabel("Bandwidth (GiB/s)", color="tab:blue")
    ax_lat.set_ylabel("Latency (ns)", color="tab:red")
    ax_lat.set_ylim(0, 2500)
    ax_bw.set_ylim(0, 80)

    ax_bw.tick_params(axis="y", labelcolor="tab:blue")
    ax_lat.tick_params(axis="y", labelcolor="tab:red")
    ax_bw.grid(True)

    # Legend
    if bw_handles and lat_handles:
        if single_access_type:
            ax_bw.legend([bw_handles[0], lat_handles[0]], legend_labels[:2], loc="best")
        else:
            handles = []
            for i in range(len(bw_handles)):
                handles.append(bw_handles[i])
                handles.append(lat_handles[i])
            ax_bw.legend(handles, legend_labels, loc="best")

    fig.tight_layout()
    fig.savefig(output_file)
    plt.close(fig)

def plot_bw_latency(base_dir):
    file_path = base_dir + "/parsed_result_logs.csv"
    data = pd.read_csv(file_path)

    output_dir = os.path.dirname(file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    load_data = data[data["LoadStore Type"] == "LOAD"]
    store_data = data[data["LoadStore Type"] == "STORE"]

    load_output_files = {
        "bandwidth_vs_latency": os.path.join(output_dir, "load_bandwidth_vs_latency_plot.pdf"),
        "threads_vs_bandwidth": os.path.join(output_dir, "load_threads_vs_bandwidth_plot.pdf"),
        "threads_vs_latency": os.path.join(output_dir, "load_threads_vs_latency_plot.pdf"),
        "threads_vs_bw_latency": os.path.join(output_dir, "load_threads_vs_bw_latency_plot.pdf"),
    }

    store_output_files = {
        "bandwidth_vs_latency": os.path.join(output_dir, "store_bandwidth_vs_latency_plot.pdf"),
        "threads_vs_bandwidth": os.path.join(output_dir, "store_threads_vs_bandwidth_plot.pdf"),
        "threads_vs_latency": os.path.join(output_dir, "store_threads_vs_latency_plot.pdf"),
        "threads_vs_bw_latency": os.path.join(output_dir, "store_threads_vs_bw_latency_plot.pdf"),
    }

    if load_data.empty:
        logger.info("No LOAD data found.")
    else:
        plot_bandwidth_vs_latency_and_save(load_data, load_output_files["bandwidth_vs_latency"], "LOAD")
        plot_threads_vs_bandwidth_and_save(load_data, load_output_files["threads_vs_bandwidth"], "LOAD")
        plot_threads_vs_latency_and_save(load_data, load_output_files["threads_vs_latency"], "LOAD")
        plot_threads_vs_bw_latency_and_save(load_data, load_output_files["threads_vs_bw_latency"], "LOAD")

    if store_data.empty:
        logger.info("No STORE data found.")
    else:
        plot_bandwidth_vs_latency_and_save(store_data, store_output_files["bandwidth_vs_latency"], "STORE")
        plot_threads_vs_bandwidth_and_save(store_data, store_output_files["threads_vs_bandwidth"], "STORE")
        plot_threads_vs_latency_and_save(store_data, store_output_files["threads_vs_latency"], "STORE")
        plot_threads_vs_bw_latency_and_save(store_data, store_output_files["threads_vs_bw_latency"], "STORE")


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        logger.error(
            "Usage: python bw_latency_plot.py <result_dir_1> [<result_dir_2> ...]\n"
            "Each result_dir must contain parsed_result_logs.csv"
        )
        return 2

    had_error = False
    for base_dir in argv[1:]:
        base_dir = os.path.abspath(base_dir)
        csv_path = os.path.join(base_dir, "parsed_result_logs.csv")
        if not os.path.exists(csv_path):
            logger.error(f"Missing parsed_result_logs.csv: {csv_path}")
            had_error = True
            continue

        logger.info(f"Plotting from: {csv_path}")
        try:
            plot_bw_latency(base_dir)
        except Exception as e:
            logger.exception(f"Failed to plot for {base_dir}: {e}")
            had_error = True

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))

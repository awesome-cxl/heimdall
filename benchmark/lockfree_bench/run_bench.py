import datetime
import json
import os
import re

import invoke
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

import benchmark.basic_performance.scripts.utils.dvfs as bp_utils_dvfs
import benchmark.basic_performance.scripts.utils.prefetch as bp_utils_prefetch
import heimdall.utils.cmd as h_utils_cmd
import heimdall.utils.path as h_utils_path


def install_deps():
    with h_utils_path.chdir(h_utils_path.get_workspace_path() / "benchmark/lockfree_bench"):
        h_utils_cmd.run("mkdir -p downloads")
        h_utils_cmd.run("mkdir -p libs")
        h_utils_cmd.run("mkdir -p results")

        # install python packages using apt
        # h_utils_cmd.run("apt install -y python3-numpy python3-pandas", True)

        # install boost using apt
        # install libcds using apt
        h_utils_cmd.run("apt install -y libboost-all-dev libcds-dev", True)

        # install cxxopt from github
        h_utils_cmd.run("git clone https://github.com/jarro2783/cxxopts.git libs/cxxopt")

        # install folly from github
        # h_utils_cmd.run("apt install -y libgoogle-glog-dev", True)
        h_utils_cmd.run("git clone https://github.com/facebook/folly.git downloads/folly")
        h_utils_cmd.run("mkdir -p libs/folly")
        with h_utils_path.chdir("downloads/folly"):
            h_utils_cmd.run("git checkout v2025.02.10.00")
            h_utils_cmd.run(
                "./build/fbcode_builder/getdeps.py install-system-deps --recursive",
                True,
            )

            PYTHON_CPLUS_INCLUDE_PATHs = h_utils_cmd.run("python3-config --includes").stdout.strip()
            PYTHON_CPLUS_INCLUDE_PATHs = PYTHON_CPLUS_INCLUDE_PATHs.split()
            CPLUS_INCLUDE_PATH = h_utils_cmd.run("echo $CPLUS_INCLUDE_PATH").stdout.strip()
            for PYTHON_CPLUS_INCLUDE_PATH in PYTHON_CPLUS_INCLUDE_PATHs:
                CPLUS_INCLUDE_PATH = CPLUS_INCLUDE_PATH + ":" + PYTHON_CPLUS_INCLUDE_PATH[2:]
            logger.info(f"CPLUS_INCLUDE_PATH: {CPLUS_INCLUDE_PATH}")

            h_utils_cmd.run(
                f"CPLUS_INCLUDE_PATH={CPLUS_INCLUDE_PATH} "
                "./build/fbcode_builder/getdeps.py "
                "--num-jobs=$(nproc) "
                "--install-prefix=$(realpath ../../libs/folly) "
                "build"
            )

        # install junction from github
        h_utils_cmd.run("git clone https://github.com/preshing/junction.git downloads/junction")
        h_utils_cmd.run("git clone https://github.com/preshing/turf.git downloads/turf")
        h_utils_cmd.run("mkdir -p libs/junction")
        with h_utils_path.chdir("downloads/junction"):
            h_utils_cmd.run("mkdir build")
            with h_utils_path.chdir("build"):
                h_utils_cmd.run(
                    "cmake -DCMAKE_INSTALL_PREFIX=$(realpath ../../../libs/junction) -DJUNCTION_WITH_SAMPLES=OFF .."
                )
                h_utils_cmd.run("cmake --build . --target install --config RelWithDebInfo")

        # install tervel from github
        # run_command("git clone https://github.com/ucf-cs/tervel downloads/tervel")
        # run_command("sudo apt install libgflags-dev")


def build():
    with h_utils_path.chdir(h_utils_path.get_workspace_path() / "benchmark/lockfree_bench"):
        h_utils_cmd.run("make clean && make")


def run(machine: str, timestamp: str, results: map):
    with h_utils_path.chdir(h_utils_path.get_workspace_path() / "benchmark/lockfree_bench"):
        
        loop_rounds = 1000000

        if machine == "github-workflow":
            # Reduce loop rounds and do not set those system/hardware settings that are not available in a github workflow container
            loop_rounds = 2
        else:
            # disable automatic numa balancing globally
            h_utils_cmd.run("bash -c 'echo 0 | tee /proc/sys/kernel/numa_balancing'", sudo=True)

            bp_utils_prefetch.set_prefetcher("on")
            # bp_utils_prefetch.set_prefetcher("off")

            # set cpu scaling governor to performance mode
            bp_utils_dvfs.set_cpu_boost("performance")


        ds_configs = {
            "queue": ["boost_spsc_queue", "boost_mpmc_queue"],
            "map": [
                "folly_atomichashmap_map",
                "junction_linearmap_map",
                "junction_leapfrogmap_map",
                "libcds_michaelhashmap_map",
                # "libcds_feldmanhashmap_map", # too slow
                # "libcds_skiplistmap_map", # too slow
                # "libcds_bronsonavltreemap_map", # too slow
                # "junction_grampamap_map", # not working
            ],
        }

        # {
        #   machine_name: {
        #       numa_config_name: [
        #           setter_core,
        #           getter_core,
        #           setter_numa_node,
        #           getter_numa_node,
        #           ds_numa_node
        #       ]
        #   }
        # }
        numa_configs = {
            "basic": {
                "same_local_DIMM": [0, 1, 0, 0, 0],
            },
            "github-workflow": {
                "same_local_DIMM": [0, 1, 0, 0, 0],
            },
            "agamotto": {
                "same_local_DIMM": [0, 1, 0, 0, 0],
                "same_remote_DIMM": [0, 1, 0, 0, 1],
                "same_local_CXL": [0, 1, 0, 0, 2],
                "same_remote_CXL": [20, 21, 1, 1, 2],
                "diff_setter_DIMM": [0, 20, 0, 1, 0],
                "diff_getter_DIMM": [0, 20, 0, 1, 1],
                "diff_setter_CXL": [0, 20, 0, 1, 2],
                "diff_getter_CXL": [20, 0, 1, 0, 2],
            },
            # "stormbreaker": {
            #     "same_local_DIMM": [0, 1, 0, 0, 0],
            #     "same_remote_DIMM": [0, 1, 0, 0, 2],
            #     "same_local_CXL": [0, 1, 0, 0, 4],
            #     "same_remote_CXL": [20, 21, 2, 2, 4],
            #     "diff_setter_DIMM": [0, 20, 0, 2, 0],
            #     "diff_getter_DIMM": [0, 20, 0, 2, 2],
            #     "diff_setter_CXL": [0, 20, 0, 2, 4],
            #     "diff_getter_CXL": [20, 0, 2, 0, 4],
            # },
            "titan": {
                "same_local_DIMM": [0, 1, 0, 0, 0],
                "same_remote_DIMM": [0, 1, 0, 0, 1],
                "same_local_CXL": [0, 1, 0, 0, 2],
                "same_remote_CXL": [32, 33, 1, 1, 2],
                "diff_setter_DIMM": [0, 32, 0, 1, 0],
                "diff_getter_DIMM": [0, 32, 0, 1, 1],
                "diff_setter_CXL": [0, 32, 0, 1, 2],
                "diff_getter_CXL": [32, 0, 1, 0, 2],
            },
        }

        ds_size_mbs = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
        # ds_size_mbs = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
        # ds_size_mbs = [8, 16, 32]

        log_file = f"results/log_{machine}_{timestamp}"
        with open(log_file, "w") as f:
            for ds, ds_types in ds_configs.items():
                results[ds] = {}
                for ds_type in ds_types:
                    results[ds][ds_type] = {}
                    for numa_config_name, numa_config in numa_configs[machine].items():
                        results[ds][ds_type][numa_config_name] = {}
                        for ds_size_mb in ds_size_mbs:
                            cmd = (
                                f"./bench "
                                f"--ds_type {ds_type} "
                                f"--ds_size_mb {ds_size_mb} "
                                f"--loop_rounds {loop_rounds} "
                                f"--setter_core {numa_config[0]} "
                                f"--getter_core {numa_config[1]} "
                                f"--setter_numa_node {numa_config[2]} "
                                f"--getter_numa_node {numa_config[3]} "
                                f"--ds_numa_node {numa_config[4]}"
                            )

                            time_vals = []
                            time_val_get = 0
                            second_try_times = 0
                            max_second_try_times = 20
                            timeout_sec = None
                            if ds_size_mb <= 64:
                                timeout_sec = 10
                            elif ds_size_mb <= 256:
                                timeout_sec = 60

                            while time_val_get < 10:
                                try:
                                    stdout = h_utils_cmd.run(cmd, timeout=timeout_sec).stdout

                                    time_pattern = re.compile(r"^\s*([\d]+)\s*ns", re.MULTILINE)
                                    time_strs = time_pattern.findall(stdout)
                                    time_vals.extend([float(time_str) for time_str in time_strs])
                                    time_val_get += 1

                                    f.write(
                                        f"Config: {ds} {ds_type} "
                                        f"{numa_config_name} {ds_size_mb}MB\n"
                                        f"Results got: {time_val_get}\n"
                                        f"Command: {cmd}\n"
                                        f"Output: {stdout}\n"
                                    )
                                except invoke.exceptions.CommandTimedOut as e:
                                    logger.info(f"Command did not complete within {e.timeout} seconds!")
                                    second_try_times += 1
                                    if second_try_times > max_second_try_times:
                                        logger.info(
                                            f"Max retry times reached: "
                                            f"{max_second_try_times} "
                                            f"Results got: {time_val_get}"
                                        )
                                        f.write(
                                            f"Config: {ds} {ds_type} "
                                            f"{numa_config_name} {ds_size_mb}MB\n"
                                            f"Results got: {time_val_get + 1}\n"
                                            f"Max retry times reached: "
                                            f"{max_second_try_times}\n"
                                        )
                                        break
                                    else:
                                        logger.info(
                                            f"Retry command, retry times: "
                                            f"{second_try_times} "
                                            f"Results got: {time_val_get}"
                                        )
                                        f.write(
                                            f"Config: {ds} {ds_type} "
                                            f"{numa_config_name} {ds_size_mb}MB\n"
                                            f"Results got: {time_val_get + 1}\n"
                                            f"Retry times: {second_try_times}\n"
                                        )
                                except Exception as e:
                                    time_val_get += 1

                                    logger.debug(str(e))
                                    f.write(
                                        f"Config: {ds} {ds_type} "
                                        f"{numa_config_name} {ds_size_mb}MB\n"
                                        f"Error msg: {str(e)}\n"
                                    )

                            df = pd.DataFrame(time_vals, columns=["time"])
                            avg_time = df["time"].mean()
                            results[ds][ds_type][numa_config_name][ds_size_mb] = avg_time

                        res_file = f"results/res_{machine}_{timestamp}"
                        with open(res_file, "w", encoding="utf-8") as r_f:
                            json.dump(
                                results,
                                r_f,
                                indent=4,
                                ensure_ascii=False,
                                sort_keys=True,
                            )

        # pprint(results[ds])
        res_file = f"results/res_{machine}_{timestamp}"
        with open(res_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False, sort_keys=True)


def plot_res(machine: str, timestamp: str, results: map):
    with h_utils_path.chdir(h_utils_path.get_workspace_path() / "benchmark/lockfree_bench"):
        figs_dir = f"results/fig_{machine}_{timestamp}"
        os.makedirs(figs_dir, exist_ok=True)

        for ds, ds_types_map in results.items():
            for ds_type, numa_configs_map in ds_types_map.items():
                # Get all unique sizes and patterns
                numa_configs = list(numa_configs_map.keys())
                sizes = sorted([int(size) for size in numa_configs_map[numa_configs[0]].keys()])
                numa_config_patterns = [
                    "same_local",
                    "same_remote",
                    "diff_setter",
                    "diff_getter",
                ]

                # Create figure with large size
                plt.figure(figsize=(20, 10))

                # Calculate bar positions
                num_patterns = len(numa_config_patterns)
                bar_width = 1.2
                group_spacing = (num_patterns * 2 + 2.5) * bar_width
                x_positions = np.arange(len(sizes)) * group_spacing

                # Colors for different patterns
                colors = ["green", "purple", "blue", "orange"]

                # First plot all bars
                for i, pattern in enumerate(numa_config_patterns):
                    dimm_numa_config = f"{pattern}_DIMM"
                    cxl_numa_config = f"{pattern}_CXL"

                    dimm_times = [numa_configs_map[dimm_numa_config][str(size)] / 1000000 for size in sizes]
                    cxl_times = [numa_configs_map[cxl_numa_config][str(size)] / 1000000 for size in sizes]

                    plt.bar(
                        x_positions + i * bar_width,
                        dimm_times,
                        bar_width,
                        label=dimm_numa_config,
                        alpha=0.8,
                        color=colors[i],
                    )
                    plt.bar(
                        x_positions + (i + num_patterns) * bar_width,
                        cxl_times,
                        bar_width,
                        label=cxl_numa_config,
                        alpha=0.8,
                        color=colors[i],
                        hatch="//",
                    )

                # Customize the plot
                # plt.yscale('log')
                plt.grid(True, which="both", ls="-", alpha=0.2)
                plt.xlabel("Size (MB)", fontsize=18)
                plt.ylabel("Time (ms)", fontsize=18)
                plt.title(f"{ds_type} Concurrent 1M set/get", fontsize=24)

                # Set x-axis ticks
                plt.xticks(x_positions + (num_patterns * bar_width), sizes, fontsize=18)

                # Set y-axis ticks and grid
                plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ",")))
                plt.gca().yaxis.set_minor_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ",")))
                # plt.gca().yaxis.set_major_locator(
                # plt.LogLocator(base=10, numticks=15)
                # )
                # plt.gca().yaxis.set_minor_locator(
                # plt.LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=15)
                # )
                plt.yticks(fontsize=18)

                # Add legend with larger font
                plt.legend(fontsize=16, loc="upper right", bbox_to_anchor=(1.2, 1))

                # Adjust layout
                plt.tight_layout()

                # Show the plot
                # plt.show()
                plt.savefig(
                    f"{figs_dir}/fig_{ds}_{ds_type}_bar.pdf",
                    bbox_inches="tight",  # Fits figure tightly
                    dpi=300,  # Higher resolution
                    format="pdf",  # Explicitly specify format
                )

                # Create figure with a larger size
                plt.figure(figsize=(20, 10))

                # Plot each metric
                markers = ["o", "s", "^", "D"]

                for pattern, marker, color in zip(numa_config_patterns, markers, colors):
                    dimm_numa_config = f"{pattern}_DIMM"
                    cxl_numa_config = f"{pattern}_CXL"

                    # Get values for both CXL and DIMM
                    dimm_times = [numa_configs_map[dimm_numa_config][str(size)] / 1000000 for size in sizes]
                    cxl_times = [numa_configs_map[cxl_numa_config][str(size)] / 1000000 for size in sizes]

                    # Plot CXL and DIMM lines with correct format string
                    plt.plot(
                        sizes,
                        dimm_times,
                        color=color,
                        linestyle="-",
                        linewidth=4,
                        label=dimm_numa_config,
                        marker=marker,
                        markersize=8,
                    )
                    plt.plot(
                        sizes,
                        cxl_times,
                        color=color,
                        linestyle=":",
                        linewidth=4,
                        label=cxl_numa_config,
                        marker=marker,
                        markersize=8,
                    )

                # Customize the plot
                plt.xscale("log", base=2)
                # plt.yscale('log')

                plt.grid(True, which="both", ls="-", alpha=0.2)
                plt.xlabel("Size (MB)", fontsize=18)
                plt.ylabel("Time (ms)", fontsize=18)
                plt.title(f"{ds_type} Concurrent 1M set/get", fontsize=24)

                # Set x-axis ticks
                plt.xticks(fontsize=18)

                # Set y-axis ticks and grid
                plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ",")))
                plt.gca().yaxis.set_minor_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ",")))
                # plt.gca().yaxis.set_major_locator(
                # plt.LogLocator(base=10, numticks=15)
                # )
                # plt.gca().yaxis.set_minor_locator(
                # plt.LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=15)
                # )
                plt.yticks(fontsize=18)

                # Add legend with larger font
                plt.legend(fontsize=16, loc="upper right", bbox_to_anchor=(1.2, 1))

                # Adjust layout to prevent label cutoff
                plt.tight_layout()

                # Show the plot
                # plt.show()
                plt.savefig(
                    f"{figs_dir}/fig_{ds}_{ds_type}_line.pdf",
                    bbox_inches="tight",  # Fits figure tightly
                    dpi=300,  # Higher resolution
                    format="pdf",  # Explicitly specify format
                )


def plot(machine: str, timestamp: str):
    with h_utils_path.chdir(h_utils_path.get_workspace_path() / "benchmark/lockfree_bench"):
        res_file = f"results/res_{machine}_{timestamp}"
        try:
            with open(res_file, encoding="utf-8") as f:
                results = json.load(f)
                plot_res(machine, timestamp, results)
        except FileNotFoundError:
            print("File not found")
        except json.JSONDecodeError:
            print("Invalid JSON format")


if __name__ == "__main__":
    machine = "agamotto"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results = {}

    install_deps()
    build()
    run(machine, timestamp, results)
    plot(machine, timestamp)

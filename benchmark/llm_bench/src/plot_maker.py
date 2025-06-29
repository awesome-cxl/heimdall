import os
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as e:
    print(f"Error: Required dependencies not found. Please install: {e}")
    print("Run: pip install matplotlib pandas")
    sys.exit(1)

def get_script_dir():
    """Get the directory where this script is located"""
    return Path(__file__).parent.absolute()

def get_logs_base_dir():
    """Get the logs base directory relative to this script"""
    script_dir = get_script_dir()
    # Go up from src/ to llm_bench/ then to logs/
    logs_base = script_dir.parent / "logs"
    return logs_base

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist"""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def main():
    print("Starting plot generation...")
    
    # Get base directory for logs
    logs_base = get_logs_base_dir()
    print(f"Looking for logs in: {logs_base}")
    
    # Check if logs directory exists
    if not logs_base.exists():
        print(f"Warning: Logs directory does not exist: {logs_base}")
        print("No benchmark results found. Please run benchmarks first using:")
        print("  uv run heimdall bench run llm [pytorch|llamacpp|vllm_cpu|vllm_gpu]")
        return False
    
    # Gather all subdirectories under logs_base, excluding 'plot'
    try:
        folders = [f.name for f in logs_base.iterdir() if f.is_dir() and f.name != "plot"]
        print(f"Found folders: {folders}")
    except Exception as e:
        print(f"Error reading logs directory: {e}")
        return False
    
    if not folders:
        print("No data folders found in logs directory")
        return False
    
    # Directory to save the resulting figures
    result_dir = ensure_directory_exists(logs_base / "plot")
    print(f"Saving plots to: {result_dir}")
    
    # Mapping from (cpu_bind, mem_bind) to descriptive labels
    labels_map = {
        (-1, 0): "Default DIMM (No CPU Bind)",
        (-1, 2): "Default CXL (No CPU Bind)",
        (0, 0): "Local DIMM",
        (0, 2): "Local CXL",
        (1, 0): "Remote DIMM",
        (1, 2): "Remote CXL",
    }
    
    # Define a color map to ensure DIMM-related labels share a similar tone (blue)
    # and CXL-related labels share a similar tone (green)
    color_map = {
        "Default DIMM (No CPU Bind)": "#9ecae1",
        "Local DIMM": "#4292c6",
        "Remote DIMM": "#08519c",
        "Default CXL (No CPU Bind)": "#a1d99b",
        "Local CXL": "#31a354",
        "Remote CXL": "#006d2c",
    }
    
    def convert_cpu(cpu_value):
        """
        Convert CPU value (string) to an integer code:
        - 'nocpubind' -> -1
        - 'cpu0' or '0' -> 0
        - 'cpu1' or '1' -> 1
        Returns None for unrecognized values.
        """
        cpu_str = str(cpu_value).lower().strip()
        if cpu_str == "nocpubind":
            return -1
        elif cpu_str in ["cpu0", "0"]:
            return 0
        elif cpu_str in ["cpu1", "1"]:
            return 1
        else:
            return None
    
    plots_generated = 0
    
    # Process each folder to find test_results.csv
    for folder in folders:
        file_path = logs_base / folder / "test_results.csv"
        
        print(f"Processing: {file_path}")
        
        if not file_path.exists():
            print(f"  - Skipped: CSV file not found")
            continue
            
        try:
            # Load CSV file using '|' as a separator
            df = pd.read_csv(file_path, sep="|", on_bad_lines="skip")
            print(f"  - Loaded {len(df)} rows")
        except Exception as e:
            print(f"  - Error loading CSV: {e}")
            continue
        
        # Check if the required columns exist
        if "cpu" not in df.columns or "mem" not in df.columns:
            print(f"  - Skipped: Required columns (cpu, mem) not found. Available: {list(df.columns)}")
            continue
        
        # Create a tuple (cpu_bind, mem_bind) by converting the CPU value
        df["cpu_mem_tuple"] = df.apply(lambda row: (convert_cpu(row["cpu"]), int(row["mem"])), axis=1)
        
        # Remove rows where the CPU conversion resulted in None
        df = df[df["cpu_mem_tuple"].apply(lambda x: x[0] is not None)]
        
        # Map the tuple (cpu_bind, mem_bind) to a descriptive label
        df["cpu_mem"] = df["cpu_mem_tuple"].map(labels_map)
        
        # Filter out any tuples not found in labels_map
        df = df[df["cpu_mem_tuple"].isin(labels_map.keys())]
        
        if df.empty:
            print(f"  - Skipped: No valid data after conversion")
            continue
        
        # Sort by the label order to keep a consistent x-axis
        df["order"] = df["cpu_mem_tuple"].map(lambda x: list(labels_map.keys()).index(x))
        df = df.sort_values("order").drop("order", axis=1)
        
        # If tokens_per_sec is not available, skip
        if "tokens_per_sec" not in df.columns:
            print(f"  - Skipped: tokens_per_sec column not found")
            continue
        
        # Check if latency_per_token is available
        has_latency = "latency_per_token" in df.columns
        
        # Assign colors based on cpu_mem labels
        df["color"] = df["cpu_mem"].map(color_map)
        
        try:
            if has_latency:
                # Create two subplots side by side
                fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(14, 6))
                
                # First subplot: tokens_per_sec
                axes[0].bar(df["cpu_mem"], df["tokens_per_sec"], color=df["color"])
                axes[0].set_xlabel("CPU & MEM Combination")
                axes[0].set_ylabel("Tokens per Second")
                axes[0].set_title("Tokens per Second")
                axes[0].tick_params(axis="x", rotation=45)
                
                # Second subplot: latency_per_token
                axes[1].bar(df["cpu_mem"], df["latency_per_token"], color=df["color"])
                axes[1].set_xlabel("CPU & MEM Combination")
                axes[1].set_ylabel("Latency per Token")
                axes[1].set_title("Latency per Token")
                axes[1].tick_params(axis="x", rotation=45)
                
                plt.suptitle(f"{folder}/test_results.csv", fontsize=16)
                plt.tight_layout(rect=[0, 0, 1, 0.93])
            else:
                # If only tokens_per_sec is available, create a single plot
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(df["cpu_mem"], df["tokens_per_sec"], color=df["color"])
                ax.set_xlabel("CPU & MEM Combination")
                ax.set_ylabel("Tokens per Second")
                ax.set_title("Tokens per Second")
                ax.tick_params(axis="x", rotation=45)
                
                plt.suptitle(f"{folder}/test_results.csv", fontsize=16)
                plt.tight_layout(rect=[0, 0, 1, 0.93])
            
            # Save the figure
            output_filename = f"figure_{folder}_test_results.png"
            output_path = result_dir / output_filename
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            print(f"  - Generated plot: {output_path}")
            plots_generated += 1
            
        except Exception as e:
            print(f"  - Error generating plot: {e}")
            continue
    
    print(f"\nPlot generation completed! Generated {plots_generated} plots in {result_dir}")
    return plots_generated > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

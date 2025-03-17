import os
import pandas as pd
import matplotlib.pyplot as plt

# Base directory for logs
logs_base = os.path.join("benchmark/llm_bench", "logs")

# Gather all subdirectories under logs_base, excluding 'plot'
folders = [
    f for f in os.listdir(logs_base)
    if os.path.isdir(os.path.join(logs_base, f)) and f != 'plot'
]

# Directory to save the resulting figures
result_dir = os.path.join("benchmark/llm_bench", "logs", "plot")
if not os.path.exists(result_dir):
    os.makedirs(result_dir, exist_ok=True)

# Mapping from (cpu_bind, mem_bind) to descriptive labels
labels_map = {
    (-1, 0): "Default DIMM (No CPU Bind)",
    (-1, 2): "Default CXL (No CPU Bind)",
    (0, 0):  "Local DIMM",
    (0, 2):  "Local CXL",
    (1, 0):  "Remote DIMM",
    (1, 2):  "Remote CXL",
}

# Define a color map to ensure DIMM-related labels share a similar tone (blue)
# and CXL-related labels share a similar tone (green)
color_map = {
    "Default DIMM (No CPU Bind)": "#9ecae1",
    "Local DIMM":                 "#4292c6",
    "Remote DIMM":               "#08519c",
    "Default CXL (No CPU Bind)": "#a1d99b",
    "Local CXL":                 "#31a354",
    "Remote CXL":                "#006d2c",
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

# Process each folder to find test_results.csv
for folder in folders:
    file_path = os.path.join(logs_base, folder, "test_results.csv")
    
    if os.path.exists(file_path):
        try:
            # Load CSV file using '|' as a separator
            df = pd.read_csv(file_path, sep='|', on_bad_lines='skip')
        except Exception as e:
            # If there's an error while loading, skip this folder
            continue
        
        # Check if the required columns exist
        if 'cpu' not in df.columns or 'mem' not in df.columns:
            continue
        
        # Create a tuple (cpu_bind, mem_bind) by converting the CPU value
        df['cpu_mem_tuple'] = df.apply(lambda row: (convert_cpu(row['cpu']), int(row['mem'])), axis=1)
        
        # Remove rows where the CPU conversion resulted in None
        df = df[df['cpu_mem_tuple'].apply(lambda x: x[0] is not None)]
        
        # Map the tuple (cpu_bind, mem_bind) to a descriptive label
        df['cpu_mem'] = df['cpu_mem_tuple'].map(labels_map)
        
        # Filter out any tuples not found in labels_map
        df = df[df['cpu_mem_tuple'].isin(labels_map.keys())]
        
        if df.empty:
            print(f"No valid data in {file_path} after conversion: {df['cpu_mem_tuple'].unique()}")
            continue
        
        # Sort by the label order to keep a consistent x-axis
        df['order'] = df['cpu_mem_tuple'].map(lambda x: list(labels_map.keys()).index(x))
        df = df.sort_values('order').drop('order', axis=1)
        
        # If tokens_per_sec is not available, skip
        if 'tokens_per_sec' not in df.columns:
            continue
        
        # Check if latency_per_token is available
        has_latency = ('latency_per_token' in df.columns)
        
        # Assign colors based on cpu_mem labels
        df['color'] = df['cpu_mem'].map(color_map)
        
        if has_latency:
            # Create two subplots side by side
            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(14, 6))
            
            # First subplot: tokens_per_sec
            axes[0].bar(df['cpu_mem'], df['tokens_per_sec'], color=df['color'])
            axes[0].set_xlabel("CPU & MEM Combination")
            axes[0].set_ylabel("Tokens per Second")
            axes[0].set_title("Tokens per Second")
            axes[0].tick_params(axis='x', rotation=45)
            
            # Second subplot: latency_per_token
            axes[1].bar(df['cpu_mem'], df['latency_per_token'], color=df['color'])
            axes[1].set_xlabel("CPU & MEM Combination")
            axes[1].set_ylabel("Latency per Token")
            axes[1].set_title("Latency per Token")
            axes[1].tick_params(axis='x', rotation=45)
            
            plt.suptitle(f"{folder}/test_results.csv", fontsize=16)
            plt.tight_layout(rect=[0, 0, 1, 0.93])
        else:
            # If only tokens_per_sec is available, create a single plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(df['cpu_mem'], df['tokens_per_sec'], color=df['color'])
            ax.set_xlabel("CPU & MEM Combination")
            ax.set_ylabel("Tokens per Second")
            ax.set_title("Tokens per Second")
            ax.tick_params(axis='x', rotation=45)
            
            plt.suptitle(f"{folder}/test_results.csv", fontsize=16)
            plt.tight_layout(rect=[0, 0, 1, 0.93])
        
        # Save the figure
        output_filename = f"figure_{folder}_test_results.png"
        output_path = os.path.join(result_dir, output_filename)
        plt.savefig(output_path)
        plt.close(fig)
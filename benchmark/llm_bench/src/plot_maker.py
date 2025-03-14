import os
import pandas as pd
import matplotlib.pyplot as plt

# Define the base logs directory relative to the current working directory (benchmark/llm_bench/src)
logs_base = os.path.join("..", "logs")

# List all subdirectories under logs_base
folders = [f for f in os.listdir(logs_base) if os.path.isdir(os.path.join(logs_base, f))]

# Define a result directory to save figures (inside logs/plot)
result_dir = os.path.join("..", "logs", "plot")
if not os.path.exists(result_dir):
    os.makedirs(result_dir)

# Loop over each subfolder and process test_results.csv if it exists
for folder in folders:
    file_path = os.path.join(logs_base, folder, "test_results.csv")
    if os.path.exists(file_path):
        try:
            # Read the CSV file using '|' as the delimiter and skip bad lines if any
            df = pd.read_csv(file_path, sep='|', on_bad_lines='skip')
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
        
        # Create a new column combining 'cpu' and 'mem'
        df['cpu_mem'] = df['cpu'].astype(str) + '_' + df['mem'].astype(str)
        print(df.columns)
        # Check if the 'tokens_per_sec' column exists
        if 'tokens_per_sec' not in df.columns:
            print(f"File {file_path} doesn't contain 'tokens_per_sec' column. Skipping.")
            continue
        
        # Check if the 'latency_per_token' column exists
        has_latency = 'latency_per_token' in df.columns
        
        # Create a figure based on available columns
        if has_latency:
            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(14, 6))
            
            # Plot tokens_per_sec
            axes[0].bar(df['cpu_mem'], df['tokens_per_sec'])
            axes[0].set_xlabel("CPU & MEM Combination")
            axes[0].set_ylabel("Tokens per Second")
            axes[0].set_title("Tokens per Second")
            axes[0].tick_params(axis='x', rotation=45)
            
            # Plot latency_per_token
            axes[1].bar(df['cpu_mem'], df['latency_per_token'])
            axes[1].set_xlabel("CPU & MEM Combination")
            axes[1].set_ylabel("Latency per Token")
            axes[1].set_title("Latency per Token")
            axes[1].tick_params(axis='x', rotation=45)
            
            plt.suptitle(f"{folder}/test_results.csv", fontsize=16)
            plt.tight_layout(rect=[0, 0, 1, 0.93])
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(df['cpu_mem'], df['tokens_per_sec'])
            ax.set_xlabel("CPU & MEM Combination")
            ax.set_ylabel("Tokens per Second")
            ax.set_title("Tokens per Second")
            ax.tick_params(axis='x', rotation=45)
            plt.suptitle(f"{folder}/test_results.csv", fontsize=16)
            plt.tight_layout(rect=[0, 0, 1, 0.93])
        
        # Save the figure in the result directory with a unique filename
        output_filename = f"figure_{folder}_test_results.png"
        output_path = os.path.join(result_dir, output_filename)
        plt.savefig(output_path)
        plt.close(fig)
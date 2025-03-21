import os
import shutil  # Added import for shutil
import subprocess

import typer
from huggingface_hub import HfApi, hf_hub_download, snapshot_download
from loguru import logger

import benchmark.basic_performance.scripts.utils.utils as utils

app = typer.Typer()

def clone_repo(repo_url, clone_dir):
    if not os.path.exists(clone_dir):
        subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    else:
        logger.info(f"{clone_dir} already exists. Skipping clone.")

def check_huggingface_login():
    """Check if the user is logged into Hugging Face"""
    try:
        api = HfApi()
        user_info = api.whoami()  # Verify login status
        logger.info(f"Hugging Face login verified: {user_info['name']}")
        return True
    except Exception:
        logger.error("Hugging Face login not detected! Please log in first.")
        print("\n🔴 Hugging Face login is required. Please run the following command\n")
        print("    huggingface-cli login\n")
        exit(1)

def download_dataset(dataset_dir):
    """Remove the existing dataset directory and clone the dataset repo."""
    target_dir = dataset_dir
    repo_url = "https://github.com/awesome-cxl/heimdall.git"
        
    if os.path.exists(target_dir):
        print(f"{target_dir} already exists. Removing it.")
        shutil.rmtree(target_dir)
    
    # 
    clone_cmd = [
        "git",
        "clone",
        "--filter=blob:none",
        "--sparse",
        repo_url,
        target_dir
    ]
    print("Cloning repository with sparse option...")
    subprocess.run(clone_cmd, check=True)
    
    # 
    sparse_cmd = ["git", "sparse-checkout", "set", "datasets"]
    print("Setting sparse-checkout for 'datasets' folder...")
    subprocess.run(sparse_cmd, cwd=target_dir, check=True)

    nested_dir = os.path.join(target_dir, "benchmark", "llm_bench", "datasets")
    if os.path.exists(nested_dir) and os.path.isdir(nested_dir):
        print(f"Found nested directory: {nested_dir}")
        for item in os.listdir(nested_dir):
            src_path = os.path.join(nested_dir, item)
            dst_path = os.path.join(target_dir, item)
            print(f"Moving {src_path} to {dst_path}")
            shutil.move(src_path, dst_path)
        
        nested_parent = os.path.join(target_dir, "benchmark")
        if os.path.exists(nested_parent):
            shutil.rmtree(nested_parent)
        print("Flattened repository structure to target directory.")
    
    print("Sparse checkout completed successfully.")

def ensure_git_lfs_installed(dataset_dir):
    """Check if git-lfs is installed. If not, install it."""
    if not shutil.which("git-lfs"):
        logger.info("git-lfs not found. Installing git-lfs...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "git-lfs"], check=True)
        subprocess.run(["git", "lfs", "install"], check=True)
        download_dataset(dataset_dir)
    else:
        logger.info("git-lfs is already installed.")

def ensure_package_installed(package):
    if not shutil.which(package):
        logger.info(f"{package} not found. Installing...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", package], check=True)

def setup_vllm_environment(vllm_dir):
    import re

    setup_envs_file = os.path.join(vllm_dir, "vllm/envs.py")
    with open(setup_envs_file, "r") as f:
        content = f.read()

    # Replace VLLM_TARGET_DEVICE assignment to use "cpu"
    content = re.sub(
        r'VLLM_TARGET_DEVICE: str = "cuda"',
        'VLLM_TARGET_DEVICE: str = "cpu"',
        content,
    )

    with open(setup_envs_file, "w") as f:
        f.write(content)

    setup_py_file = os.path.join(vllm_dir, "setup.py")
    with open(setup_py_file, "r") as file:
        lines = file.readlines()

    removed_line = lines.pop(539)

    if len(lines) > 539:
        lines[539] = lines[539].replace("    ", "", 1)

    with open(setup_py_file, "w") as file:
        file.writelines(lines)


def vllm_install_dependencies(machine, vllm_dir):
    if machine in ["x86", "arm"]:
        subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "gcc-12", "g++-12", "libnuma-dev"], check=True)
        subprocess.run(
            [
                "sudo", "update-alternatives", "--install", "/usr/bin/gcc", "gcc", "/usr/bin/gcc-12", "10",
                "--slave", "/usr/bin/g++", "g++", "/usr/bin/g++-12"
            ],
            check=True,
        )

        if machine == "x86":
            subprocess.run(["pip", "install", "--upgrade", "pip"], check=True)
            subprocess.run(
                ["pip", "install", "cmake>=3.26", "wheel", "packaging", "ninja", "setuptools-scm>=8", "numpy"],
                check=True,
            )
            subprocess.run(
                ["pip", "install", "-r", os.path.join(vllm_dir, "requirements-cpu.txt"),
                 "--extra-index-url", "https://download.pytorch.org/whl/cpu"],
                check=True,
            )
    elif machine == "apple":
        subprocess.run(
            ["pip", "install", "-r", os.path.join(vllm_dir, "requirements-cpu.txt")],
            check=True,
        )
    else:
        logger.error(f"Unsupported machine type: {machine}")
        exit(1)


def vllm_download_dataset(dataset_dir):
    base_url = "https://huggingface.co/datasets/anon8231489123"
    dataset_url = f"{base_url}/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json"
    dataset_path = os.path.join(dataset_dir, "ShareGPT_V3_unfiltered_cleaned_split.json")
    os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
    subprocess.run(["wget", dataset_url, "-O", dataset_path], check=True)


@app.command()
def install(config: str):
    logger.info("installing")
    # Check if the user is logged into Hugging Face before proceeding
    check_huggingface_login()

    # Ensure numactl is installed
    ensure_package_installed("numactl")

    # Setup directories for models and datasets using the globally imported os
    base_dir = os.getcwd()
    model_dir = os.path.join(base_dir, "benchmark/llm_bench/models")
    dataset_dir = os.path.join(base_dir, "benchmark/llm_bench/datasets")
    ensure_git_lfs_installed(dataset_dir)

    if config in ["pytorch"]:
        model_version = "llama3-8B"
        # Clone Meta's LLaMA repository (contains generation.py, model.py, etc.)
        repo_url = "https://github.com/meta-llama/llama3.git"
        pytorch_dir = os.path.join(os.getcwd(), "benchmark/llm_bench/llama")
        if not os.path.exists(pytorch_dir):
            subprocess.run(["git", "clone", repo_url, pytorch_dir], check=True)
            import re

            file_path = os.path.join(
                os.getcwd(), "benchmark/llm_bench/llama/llama/generation.py"
            )

            with open(file_path, "r") as f:
                content = f.read()

            # Wrap torch.cuda.set_device(line) with a CUDA availability check.
            content = re.sub(
                r"(^\s*)(torch\.cuda\.set_device\(local_rank\))",
                r"\1if torch.cuda.is_available():\n\1    \2",
                content,
                flags=re.MULTILINE,
            )

            # Replace torch.set_default_tensor_type for CPU inference.
            content = re.sub(
                r"(^\s*)torch\.set_default_tensor_type\(torch\.cuda\.HalfTensor\)",
                r"\1if torch.cuda.is_available():\n"
                r"\1    torch.set_default_tensor_type(torch.cuda.HalfTensor)\n"
                r"\1else:\n"
                r"\1    torch.set_default_tensor_type(torch.FloatTensor)",
                content,
                flags=re.MULTILINE,
            )
            # Replace explicit device="cuda" with the dynamic device variable.
            content = re.sub(r'device="cuda"', 'device="cpu"', content)
            # Replace initialization of the distributed process group.
            # If CUDA is available, use NCCL, otherwise use Gloo.
            content = re.sub(
                r'(^\s*)torch\.distributed\.init_process_group\("nccl"\)',
                r"\1if torch.cuda.is_available():\n"
                r'\1    torch.distributed.init_process_group("nccl")\n'
                r"\1else:\n"
                r'\1    torch.distributed.init_process_group("gloo")',
                content,
                flags=re.MULTILINE,
            )
            with open(file_path, "w") as f:
                f.write(content)

            print("Updated generation.py for CPU inference.")

            # Remove .cuda() calls from model.py for CPU inference.
            model_file_path = os.path.join(
                os.getcwd(), "benchmark/llm_bench/llama/llama/model.py"
            )
            with open(model_file_path, "r") as f:
                model_content = f.read()
            model_content = model_content.replace(".cuda()", "")
            with open(model_file_path, "w") as f:
                f.write(model_content)

            print("Updated model.py: Removed .cuda() calls for CPU inference.")
            subprocess.run(
                ["pip", "install", "-r", os.path.join(pytorch_dir, "requirements.txt"),
                 "--extra-index-url", "https://download.pytorch.org/whl/cpu"],
                check=True,
            )
            subprocess.run(["pip", "install", "-e", "."], check=True)

        else:
            logger.info(f"{pytorch_dir} already exists. Skipping clone.")

        # Copy src/pytorch_run_test.py into the llama folder
        src_file = os.path.join(
            base_dir, "benchmark", "llm_bench", "src", "pytorch_run_test.py"
        )
        dst_file = os.path.join(pytorch_dir, "pytorch_run_test.py")
        shutil.copy(src_file, dst_file)
        logger.info(f"Copied pytorch_run_test.py from {src_file} to {dst_file}")
        logger.info("Downloading full repository contents from Hugging Face...")
        # Set custom_model_dir to include the repository name,
        # e.g., Meta-Llama-3-8B or Meta-Llama-3-70B
        if model_version == "llama3-8B":
            repo_id = "meta-llama/Meta-Llama-3-8B"
            repo_folder = "Meta-Llama-3-8B"
        elif model_version == "llama3-70B":
            repo_id = "meta-llama/Meta-Llama-3-70B"
            repo_folder = "Meta-Llama-3-70B"
        else:
            raise ValueError(f"Unsupported model_version: {model_version}")

        custom_model_dir = os.path.join(model_dir, "meta-llama", repo_folder)
        os.makedirs(custom_model_dir, exist_ok=True)
        if os.listdir(custom_model_dir):
            print(f"{custom_model_dir} already contains files. Skipping clone.")
        else:
            # Download only the files under "original/" similar to:
            snapshot_download(
                repo_id=repo_id,
                local_dir=custom_model_dir,
                local_dir_use_symlinks=False,
                allow_patterns=["original/*"],
            )
        original_dir = os.path.join(custom_model_dir, "original")
        if os.path.isdir(original_dir):
            for item in os.listdir(original_dir):
                shutil.move(os.path.join(original_dir, item), custom_model_dir)
            shutil.rmtree(original_dir)
            logger.info(f"Moved contents of 'original/' to {custom_model_dir}")
    elif config == "vllm":
        current_dir = os.getcwd()
        llm_bench_dir = os.path.join(current_dir, "benchmark/llm_bench")
        vllm_dir = os.path.join(llm_bench_dir, "vllm")
        vllm_url = "https://github.com/vllm-project/vllm.git"

        if not os.path.exists(vllm_dir):
            clone_repo(vllm_url, vllm_dir)
            subprocess.run(["git", "checkout", "v0.7.3"], cwd=vllm_dir, check=True)
        else:
            logger.info(f"{vllm_dir} already exists. Skipping clone.")

        machine = utils.get_architecture()
        vllm_install_dependencies(machine, vllm_dir)

        if machine in ["x86", "arm"]:
            setup_vllm_environment(vllm_dir)
            subprocess.run(
                ["python", os.path.join(vllm_dir, "setup.py"), "install"],
                check=True,
                cwd=vllm_dir,
            )
        elif machine == "apple":
            subprocess.run(["pip", "install", "-e", "."], check=True, cwd=vllm_dir)

        vllm_download_dataset(dataset_dir)

    elif config in ["llamacpp"]:
        model_version = "llama3-8B"
        # Clone the repository directly into a folder named "llama.cpp"
        repo_url = "https://github.com/ggerganov/llama.cpp"
        project_dir = os.path.join(os.getcwd(), "benchmark", "llm_bench", "llama.cpp")

        clone_repo(repo_url, project_dir)

        # Define a directory to store downloaded models inside the llama.cpp folder
        project_dir = os.path.join(os.getcwd(), "benchmark/llm_bench/llama.cpp")
        custom_model_dir = os.path.join(model_dir, "QuantFactory")
        os.makedirs(custom_model_dir, exist_ok=True)

        # Download the Meta-Llama-3-8B.Q4_K_M.gguf model from  Hugging Face
        if model_version == "llama3-8B":
            repo_id = "QuantFactory/Meta-Llama-3-8B-GGUF"
            filename = "Meta-Llama-3-8B.Q4_K_M.gguf"
        elif model_version == "llama3-70B":
            repo_id = "QuantFactory/Meta-Llama-70B-GGUF"
            filename = "Meta-Llama-3-70B.Q4_K_M.gguf"
        else:
            raise ValueError(f"Unsupported model_version: {model_version}")

        model_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=custom_model_dir,
            local_dir_use_symlinks=False,
        )
        print(f"Quantized model downloaded to: {model_path}")
        # Set the project directory to the cloned folder "llama.cpp"
        # Build the project for CPU only
        subprocess.run(["cmake", "-B", "build"], cwd=project_dir, check=True)
        # Then, build the project with Release configuration
        subprocess.run(
            ["cmake", "--build", "build", "--config", "Release"],
            cwd=project_dir,
            check=True,
        )

    else:
        logger.error(f"this is the unknown task: {config}")
    pass


@app.command()
def build(config: str):
    pass


@app.command()
def run(config: str):
    logger.info("Running")
    script_map = {
        "pytorch": "pytorch_run_test.sh",
        "vllm": "vllm_run_test.sh",
        "llamacpp": "llamacpp_run_test.sh"
    }
    base_dir = os.path.join(os.path.dirname(__file__), "scripts")

    if config == "all":
        for script in script_map.values():
            script_path = os.path.join(base_dir, script)
            subprocess.run(["bash", script_path], check=True)
    elif config in script_map:
        script_path = os.path.join(base_dir, script_map[config])
        subprocess.run(["bash", script_path], check=True)
    else:
        logger.error(f"this is the unknown task: {config}")
    pass


@app.command
def plot(config: str):
    logger.info("plotting")
    pass

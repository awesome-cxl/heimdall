import os
import shutil  # Added import for shutil
import subprocess

import typer
from huggingface_hub import HfApi, hf_hub_download, snapshot_download
from loguru import logger

import benchmark.basic_performance.scripts.utils.utils as utils

app = typer.Typer()


def ensure_venv():
    """Ensure .venv exists, create if not"""
    if not os.path.exists(".venv"):
        logger.info("Creating virtual environment...")
        subprocess.run(["uv", "venv", "--python", "3.12", "--seed"], check=True)
        logger.info("Virtual environment created successfully")
    else:
        logger.info("Virtual environment already exists")


def run_in_venv(command, cwd=None):
    """Run command in virtual environment"""
    ensure_venv()
    
    # Use venv python/bash instead of system ones
    venv_python = os.path.abspath(".venv/bin/python")
    venv_bash = os.path.abspath(".venv/bin/bash")
    
    if command[0] == "python":
        command[0] = venv_python
    elif command[0] == "bash":
        command[0] = venv_bash
        # For bash scripts, we need to source the venv activation
        if len(command) > 1 and command[1].endswith('.sh'):
            # Create a wrapper command that activates venv and runs the script
            script_path = command[1]
            wrapper_cmd = f"source .venv/bin/activate && bash {script_path}"
            command = ["bash", "-c", wrapper_cmd]
    
    subprocess.run(command, check=True, cwd=cwd)


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
    clone_cmd = ["git", "clone", "--filter=blob:none", "--sparse", repo_url, target_dir]
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
    """Check if git-lfs is installed. If not, install it. Also handle LFS download failures."""
    if not shutil.which("git-lfs"):
        logger.info("git-lfs not found. Installing git-lfs...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "git-lfs"], check=True)
        subprocess.run(["git", "lfs", "install"], check=True)
        download_dataset(dataset_dir)
    else:
        logger.info("git-lfs is already installed.")
        # Check if LFS files can be properly downloaded
        wiki_test_file = os.path.join(dataset_dir, "wiki.test.raw")
        if os.path.exists(wiki_test_file):
            # Check if file is an LFS pointer file
            with open(wiki_test_file, 'r') as f:
                first_line = f.readline().strip()
                if first_line.startswith("version https://git-lfs.github.com/spec/"):
                    logger.warning("wiki.test.raw is an LFS pointer file, attempting to download...")
                    try:
                        # Try to pull LFS files
                        subprocess.run(["git", "lfs", "pull"], cwd=os.path.dirname(dataset_dir), check=True)
                        logger.info("LFS files downloaded successfully")
                    except subprocess.CalledProcessError as e:
                        logger.error("❌ Git LFS file download failed!")
                        logger.error("Reason: Required dataset file could not be downloaded (404 error)")
                        logger.error("Cannot proceed without valid dataset file.")
                        exit(1)


def ensure_package_installed(package):
    if not shutil.which(package):
        logger.info(f"{package} not found. Installing...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", package], check=True)


def setup_vllm_environment(vllm_dir):
    import re

    setup_envs_file = os.path.join(vllm_dir, "vllm/envs.py")
    with open(setup_envs_file) as f:
        content = f.read()

    # Replace VLLM_TARGET_DEVICE assignment to use "cpu"
    content = re.sub(
        r'VLLM_TARGET_DEVICE: str = "cuda"',
        'VLLM_TARGET_DEVICE: str = "cpu"',
        content,
    )

    # Add additional CPU-specific environment variables for v0.9.1+
    if 'VLLM_DEVICE = ' not in content:
        content += '\n# Additional CPU environment variables for v0.9.1+\n'
        content += 'VLLM_DEVICE = "cpu"\n'
        content += 'VLLM_FORCE_CPU = "1"\n'
        content += 'CUDA_VISIBLE_DEVICES = ""\n'

    with open(setup_envs_file, "w") as f:
        f.write(content)

    setup_py_file = os.path.join(vllm_dir, "setup.py")
    with open(setup_py_file) as file:
        lines = file.readlines()

    # Fix the indentation issue for CPU condition check
    if len(lines) > 539:
        # Make sure the if statement is properly indented within the elif block
        if "if envs.VLLM_TARGET_DEVICE" in lines[539]:
            lines[539] = "        if envs.VLLM_TARGET_DEVICE == \"cpu\":\n"

    with open(setup_py_file, "w") as file:
        file.writelines(lines)


def vllm_install_dependencies(machine, vllm_dir):
    if machine in ["x86", "arm"]:
        subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
        subprocess.run(
            ["sudo", "apt-get", "install", "-y", "gcc-12", "g++-12", "libnuma-dev"],
            check=True,
        )
        subprocess.run(
            [
                "sudo",
                "update-alternatives",
                "--install",
                "/usr/bin/gcc",
                "gcc",
                "/usr/bin/gcc-12",
                "10",
                "--slave",
                "/usr/bin/g++",
                "g++",
                "/usr/bin/g++-12",
            ],
            check=True,
        )

        if machine == "x86":
            subprocess.run(["pip", "install", "--upgrade", "pip"], check=True)
            subprocess.run(
                [
                    "pip",
                    "install",
                    "cmake>=3.26",
                    "wheel",
                    "packaging",
                    "ninja",
                    "setuptools-scm>=8",
                    "numpy",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "uv",
                    "pip",
                    "install",
                    "-r",
                    os.path.join(vllm_dir, "requirements", "cpu.txt"),
                    "--extra-index-url",
                    "https://download.pytorch.org/whl/cpu",
                    "--index-strategy",
                    "unsafe-best-match",
                ],
                check=True,
            )
    elif machine == "apple":
        subprocess.run(
            ["uv", "pip", "install", "-r", os.path.join(vllm_dir, "requirements", "cpu.txt"), "--index-strategy", "unsafe-best-match"],
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


def ensure_vllm_repo(vllm_dir, version="v0.9.1"):
    repo_url = "https://github.com/vllm-project/vllm.git"
    if not os.path.exists(vllm_dir):
        clone_repo(repo_url, vllm_dir)
        subprocess.run(["git", "checkout", version], cwd=vllm_dir, check=True)
    else:
        logger.info(f"{vllm_dir} already exists. Skipping clone.")


# Unified installer for vLLM source
def install_vllm_source(vllm_dir: str, gpu: bool = True):
    import os
    import subprocess

    from loguru import logger

    # GPU install path
    if gpu:
        subprocess.run(["pip", "install", "vllm"], check=True)
    else:
        machine = utils.get_architecture()
        vllm_install_dependencies(machine, vllm_dir)
        if machine in ["x86", "arm"]:
            setup_vllm_environment(vllm_dir)
            # Install additional build dependencies not in requirements
            logger.info("Installing additional build dependencies...")
            subprocess.run(
                ["uv", "pip", "install", "setuptools-scm>=8", "numpy"],
                check=True,
            )
            # Set environment variables for CPU-only build
            env = os.environ.copy()
            env["VLLM_TARGET_DEVICE"] = "cpu"
            env["CUDA_VISIBLE_DEVICES"] = ""
            env["VLLM_CPU_ONLY"] = "1"
            subprocess.run(
                ["uv", "pip", "install", "-e", "."],
                cwd=vllm_dir,
                check=True,
                env=env,
            )
        elif machine == "apple":
            subprocess.run(["pip", "install", "-e", "."], cwd=vllm_dir, check=True)
        else:
            logger.error(f"Unsupported machine type for CPU install: {machine}")
            exit(1)


def run_vllm_cpu_install_script():
    script_path = os.path.join(os.path.dirname(__file__), "scripts", "vllm_cpu_install.sh")
    if not os.path.exists(script_path):
        logger.error(f"{script_path} 파일이 존재하지 않습니다.")
        return
    run_in_venv(["bash", script_path])


@app.command()
def install(config: str):
    ensure_venv()
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

            file_path = os.path.join(os.getcwd(), "benchmark/llm_bench/llama/llama/generation.py")

            with open(file_path) as f:
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
            model_file_path = os.path.join(os.getcwd(), "benchmark/llm_bench/llama/llama/model.py")
            with open(model_file_path) as f:
                model_content = f.read()
            model_content = model_content.replace(".cuda()", "")
            with open(model_file_path, "w") as f:
                f.write(model_content)

            print("Updated model.py: Removed .cuda() calls for CPU inference.")
            subprocess.run(
                [
                    "uv",
                    "pip",
                    "install",
                    "-r",
                    os.path.join(pytorch_dir, "requirements.txt"),
                    "--extra-index-url",
                    "https://download.pytorch.org/whl/cpu",
                ],
                check=True,
            )
            subprocess.run(["uv", "pip", "install", "-e", "."], cwd=pytorch_dir, check=True)

        else:
            logger.info(f"{pytorch_dir} already exists. Skipping clone.")

        # Copy src/pytorch_run_test.py into the llama folder
        src_file = os.path.join(base_dir, "benchmark", "llm_bench", "src", "pytorch_run_test.py")
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
    elif config == "vllm_gpu":
        cwd = os.getcwd()
        vllm_dir = os.path.join(cwd, "benchmark/llm_bench", "vllm_gpu")
        ensure_vllm_repo(vllm_dir)
        # install vLLM source for GPU
        install_vllm_source(vllm_dir, gpu=True)
        vllm_download_dataset(dataset_dir)

    elif config == "vllm_cpu":
        cwd = os.getcwd()
        vllm_dir = os.path.join(cwd, "benchmark/llm_bench", "vllm_cpu")
        ensure_vllm_repo(vllm_dir)
        # install vLLM source for CPU
        run_vllm_cpu_install_script()
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
    ensure_venv()
    logger.info("Running")
    script_map = {
        "pytorch": "pytorch_run_test.sh",
        "llamacpp": "llamacpp_run_test.sh",
        "vllm_cpu": "vllm_run_test.sh",
        "vllm_gpu": "vllm_gpu_run_test.sh",
    }
    base_dir = os.path.join(os.path.dirname(__file__), "scripts")

    if config == "all":
        for script in script_map.values():
            script_path = os.path.join(base_dir, script)
            run_in_venv(["bash", script_path])
    elif config in script_map:
        script_path = os.path.join(base_dir, script_map[config])
        run_in_venv(["bash", script_path])
    else:
        logger.error(f"this is the unknown task: {config}")
    pass


@app.command()
def plot(config: str):
    ensure_venv()
    logger.info("plotting")
    src_dir = os.path.join(os.path.dirname(__file__), "src")
    plot_script = os.path.join(src_dir, "plot_maker.py")
    
    if os.path.exists(plot_script):
        run_in_venv(["python", plot_script])
        logger.info("Plot generation completed")
    else:
        logger.error(f"Plot script not found: {plot_script}")
    pass

import os
import shutil  # Added import for shutil
import subprocess

import typer
from huggingface_hub import HfApi, hf_hub_download, snapshot_download
from loguru import logger

import benchmark.basic_performance.scripts.utils.utils as utils

app = typer.Typer()


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


def ensure_package_installed(package):
    if not shutil.which(package):
        logger.info(f"{package} not found. Installing...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", package], check=True)


def clone_repo(repo_url, clone_dir):
    if not os.path.exists(clone_dir):
        subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    else:
        logger.info(f"{clone_dir} already exists. Skipping clone.")


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
                ["pip", "install", "-r", os.path.join(pytorch_dir, "requirements.txt")],
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

    elif config in ["vllm"]:
        current_dir = os.getcwd()
        llm_bench_dir = os.path.join(current_dir, "benchmark/llm_bench")
        vllm_dir = os.path.join(llm_bench_dir, "vllm")
        vllm_url = "https://github.com/vllm-project/vllm.git"
        if not os.path.exists(vllm_dir):
            clone_repo(vllm_url, vllm_dir)
        else:
            logger.info(f"{vllm_dir} already exists. Skipping clone.")
        machine = utils.get_architecture()
        if machine == "x86":
            subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "gcc-12"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "g++-12"], check=True)
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", "libnuma-dev"], check=True
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

            # Install the required packages for VLLM
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
                    "pip",
                    "install",
                    "-r",
                    os.path.join(vllm_dir, "requirements-cpu.txt"),
                    "--extra-index-url",
                    "https://download.pytorch.org/whl/cpu",
                ],
                check=True,
            )

            # python setup.py install
            import re

            setup_file = os.path.join(vllm_dir, "vllm/envs.py")
            with open(setup_file, "r") as f:
                content = f.read()

            # Replace VLLM_TARGET_DEVICE assignment to use "cpu"
            content = re.sub(
                r'VLLM_TARGET_DEVICE: str = "cuda"',
                'VLLM_TARGET_DEVICE: str = "cpu"',
                content,
            )

            with open(setup_file, "w") as f:
                f.write(content)

            subprocess.run(
                ["python", os.path.join(vllm_dir, "setup.py"), "install"],
                check=True,
                cwd=vllm_dir,
            )
        elif machine == "arm":
            subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "gcc-12"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "g++-12"], check=True)
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", "libnuma-dev"], check=True
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
            # python setup.py install
            import re

            setup_file = os.path.join(vllm_dir, "vllm/envs.py")
            with open(setup_file, "r") as f:
                content = f.read()

            # Replace VLLM_TARGET_DEVICE assignment to use "cpu"
            content = re.sub(
                r'VLLM_TARGET_DEVICE: str = "cuda"',
                'VLLM_TARGET_DEVICE: str = "cpu"',
                content,
            )

            with open(setup_file, "w") as f:
                f.write(content)

            subprocess.run(
                ["python", os.path.join(vllm_dir, "setup.py"), "install"],
                check=True,
                cwd=vllm_dir,
            )
        elif machine == "apple":
            subprocess.run(
                [
                    "pip",
                    "install",
                    "-r",
                    os.path.join(vllm_dir, "requirements-cpu.txt"),
                ],
                check=True,
            )
            subprocess.run(["pip", "install", "-e", "."], check=True, cwd=vllm_dir)
        else:
            logger.error(f"Unsupported machine type: {machine}")
            exit(1)

        # Download the VLLM model from Hugging Face
        base_url = "https://huggingface.co/datasets/anon8231489123"
        base_url2 = "ShareGPT_Vicuna_unfiltered"
        file_path = "resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json"
        dataset_url = f"{base_url}/{base_url2}/{file_path}"
        dataset_path = os.path.join(
            dataset_dir, "ShareGPT_V3_unfiltered_cleaned_split.json"
        )
        os.makedirs(
            os.path.dirname(dataset_path), exist_ok=True
        )  # Create the directory if it doesn't exist
        subprocess.run(["wget", dataset_url, "-O", dataset_path], check=True)

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
    if config in ["pytorch"]:
        script_path = os.path.join(
            os.path.dirname(__file__), "scripts", "pytorch_run_test.sh"
        )
        subprocess.run(["bash", script_path], check=True)
    elif config in ["vllm"]:
        script_path = os.path.join(
            os.path.dirname(__file__), "scripts", "vllm_run_test.sh"
        )
        subprocess.run(["bash", script_path], check=True)
    elif config in ["llamacpp"]:
        script_path = os.path.join(
            os.path.dirname(__file__), "scripts", "llamacpp_run_test.sh"
        )
        subprocess.run(["bash", script_path], check=True)
    else:
        logger.error(f"this is the unknown task: {config}")
    pass


@app.command
def plot(config: str):
    logger.info("plotting")
    pass

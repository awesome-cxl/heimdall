import typer
import os
from heimdall.utils.path import get_workspace_path, chdir
from heimdall.utils.cmd import run
from loguru import logger

app = typer.Typer()

# Define paths
SCRIPT_DIR = (
    get_workspace_path()
    / "benchmark"
    / "basic_performance"
    / "build"
    / "cache_test"
    / "module"
)

# CMake build directory
BUILD_DIR = SCRIPT_DIR / "build"

# Kernel module source directory
SRC_DIR = (
    SCRIPT_DIR / ".." / ".." / ".." / "src" / "machine" / "x86" / "pointer_chasing"
)


@app.command()
def build():
    os.makedirs(BUILD_DIR, exist_ok=True)
    with chdir(BUILD_DIR):
        logger.info("Configuring CMake...")
        run(f"cmake {SCRIPT_DIR}", sudo=True)

        logger.info("Building kernel module...")
        run("make build_kernel_module", sudo=True)


@app.command()
def clean():
    logger.info("Cleaning kernel module...")
    if not os.path.exists(BUILD_DIR):
        logger.info("No build directory found. Nothing to clean.")
        return
    with chdir(BUILD_DIR):
        run("make clean_kernel_module", sudo=True)

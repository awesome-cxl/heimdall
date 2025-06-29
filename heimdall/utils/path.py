import os
import sys
from contextlib import contextmanager
from pathlib import Path

import typer
from loguru import logger

app = typer.Typer()


@app.command()
def get_executable_path():
    """
    Get the current executable path of heimdall binary or root python script
    """

    # If built with PyInstaller, we should check for sys.executable because
    # __file__ is not available
    is_standalone = False
    if getattr(sys, "frozen", False):
        # Running in a bundled executable
        current_path = Path(sys.executable).absolute()
        is_standalone = True
    else:
        # Running as a regular script
        current_path = Path(os.path.realpath(__file__)).absolute().parent / "__init__.py"
        is_standalone = False

    logger.trace(f"Current executable path {current_path}")

    return current_path, is_standalone


@app.command()
def get_workspace_path():
    """
    Get the root workspace path: if heimdall is compiled as standalone binary,
    then use the current folder where the heimdall command is called; if
    heimdall is called from source from its git repo, then use the git repo path.
    """
    exec_path, standalone = get_executable_path()

    if standalone:
        workspace_path = Path().absolute()
    else:
        workspace_path = exec_path.parent.parent.parent

    logger.trace(f"Current workspace path is: {workspace_path}")

    return workspace_path


@contextmanager
def chdir(path: Path):
    origin = Path().absolute()
    target = Path(path).absolute()
    try:
        logger.trace(f"Switching to dir {target}")
        os.chdir(target)
        yield
    finally:
        logger.trace(f"Switching back to dir {origin}")
        os.chdir(origin)

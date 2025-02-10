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
        current_path = (
            Path(os.path.realpath(__file__)).absolute().parent / "__init__.py"
        )
        is_standalone = False

    logger.info(f"Current executable path {current_path}")

    return current_path, is_standalone


@app.command()
def get_workspace_path():
    """
    Get the root workspace path: if heimdall is compiled as standalone binary,
    then use the folder that contains heimdall binary; if heimdall is called
    from source from its git repo, then use the git repo path.
    """
    exec_path, standalone = get_executable_path()

    if standalone:
        workspace_path = exec_path.parent
    else:
        workspace_path = exec_path.parent.parent.parent

    logger.info(f"Current workspace path is: {workspace_path}")

    return workspace_path


@contextmanager
def chdir(path: Path):
    origin = Path().absolute()
    target = Path(path).absolute()
    try:
        logger.info(f"Switching to dir {target}")
        os.chdir(target)
        yield
    finally:
        logger.info(f"Switching back to dir {origin}")
        os.chdir(origin)

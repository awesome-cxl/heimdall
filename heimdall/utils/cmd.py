import os

import invoke
import typer
from loguru import logger

from heimdall.utils.path import chdir, get_executable_path, get_workspace_path

app = typer.Typer()


@app.command()
def run(cmd, sudo=False):
    if not sudo:
        return invoke.run(cmd)
    else:
        HOST_PASSWORD = os.getenv("USER_PASSWORD", "unknown_host")
        sudo_pass_responder = invoke.Responder(
            pattern=r"\[sudo\] password:.*", response=f"{HOST_PASSWORD}\n"
        )
        if HOST_PASSWORD == "unknown_host":
            logger.error(
                "Please set the user password from env 'USER_PASSWORD'"
                "and call Heimdall again"
            )
            raise typer.Exit(1)
        return invoke.sudo(
            cmd, echo=True, pty=False, warn=True, watchers=[sudo_pass_responder]
        )


@app.command()
def run_heimdall_sub_cmd(sub_cmd, sudo=False):
    exec_path, standalone = get_executable_path()

    workspace_path = get_workspace_path()
    with chdir(workspace_path):
        if standalone:
            return run(f"./{exec_path.name} {sub_cmd}", sudo=sudo)
        else:
            return run(f"poetry run heimdall {sub_cmd}", sudo=sudo)

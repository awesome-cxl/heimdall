import os

import invoke
import typer
from loguru import logger

from heimdall.utils.path import chdir, get_executable_path, get_workspace_path

app = typer.Typer()


@app.command()
def run(cmd, sudo=False, *args, **kwargs):
    kwargs.setdefault("echo", True)

    if not sudo:
        return invoke.run(cmd, *args, **kwargs)
    else:
        HOST_PASSWORD = os.getenv("USER_PASSWORD", "unknown_host")
        sudo_pass_responder = invoke.Responder(pattern=r"\[sudo\] password:.*", response=f"{HOST_PASSWORD}\n")
        if HOST_PASSWORD == "unknown_host":
            logger.error("Please set the user password from env 'USER_PASSWORD'and call Heimdall again")
            raise typer.Exit(1)

        kwargs.setdefault("pty", True)
        kwargs.setdefault("watchers", [sudo_pass_responder])
        return invoke.sudo(
            cmd,
            *args,
            **kwargs,
        )


@app.command()
def run_heimdall_sub_cmd(sub_cmd, sudo=False):
    exec_path, standalone = get_executable_path()

    workspace_path = get_workspace_path()
    with chdir(workspace_path):
        if standalone:
            return run(f"{exec_path.absolute()} {sub_cmd}", sudo=sudo)
        else:
            return run(f"uv run heimdall {sub_cmd}", sudo=sudo)

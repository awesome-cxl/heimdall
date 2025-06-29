#
# MIT License
#
# Copyright (c) 2025 Jangseon Park
# Affiliation: University of California San Diego CSE
# Email: jap036@ucsd.edu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os

import typer
from dotenv import load_dotenv
from invoke import Responder, sudo
from loguru import logger

from heimdall.utils.path import get_workspace_path

path = get_workspace_path() / "benchmark" / "basic_performance" / "env_files" / "self.env"
load_dotenv(
    dotenv_path=path,
)
HOST_PASSWORD = os.getenv("USER_PASSWORD", "unknown_host")


def run_as_sudo(cmd: str):
    cmd = f"sh -c '{cmd}'"
    sudo_pass_responder = Responder(pattern=r"\[sudo\] password:.*", response=f"{HOST_PASSWORD}\n")
    if HOST_PASSWORD == "unknown_host":
        logger.error("Please set the user password from env 'USER_PASSWORD' and callHeimdall again")
        raise typer.Exit(1)
    sudo(cmd, echo=True, pty=False, warn=True, watchers=[sudo_pass_responder])

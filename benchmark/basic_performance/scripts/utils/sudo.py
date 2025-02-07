import os

from dotenv import load_dotenv
from invoke import Responder, sudo

path = f"{os.path.dirname(os.path.realpath(__file__))}/../../env_files/self.env"

load_dotenv(
    dotenv_path=path,
)
HOST_PASSWORD = os.getenv("USER_PASSWORD", "unknown_host")


def run_as_sudo(cmd: str):
    cmd = f"sh -c '{cmd}'"
    sudo_pass_responder = Responder(
        pattern=r"\[sudo\] password:.*", response=f"{HOST_PASSWORD}\n"
    )
    sudo(cmd, echo=True, pty=False, warn=True, watchers=[sudo_pass_responder])

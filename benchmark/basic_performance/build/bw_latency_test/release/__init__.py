from benchmark.basic_performance.build.utils.build_utils import run_build
from heimdall.utils.path import get_workspace_path

import typer

app = typer.Typer()


@app.command()
def build(arch: str = None):
    build_dir = (
        get_workspace_path()
        / "benchmark"
        / "basic_performance"
        / "build"
        / "bw_latency_test"
        / "release"
        / "build"
    )

    run_build(build_dir, arch=arch, sudo=True)

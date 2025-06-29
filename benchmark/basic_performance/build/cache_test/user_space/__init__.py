import typer
from heimdall.utils.path import get_workspace_path, chdir
from heimdall.utils.cmd import run
from loguru import logger
from benchmark.basic_performance.build.utils.build_utils import (
    clean,
    make_build_dir,
    get_threads_num,
)


app = typer.Typer()


@app.command()
def build():
    logger.info("Building userspace cache test")

    build_dir = (
        get_workspace_path()
        / "benchmark"
        / "basic_performance"
        / "build"
        / "cache_test"
        / "user_space"
        / "build"
    )

    clean(build_dir)
    make_build_dir(build_dir)

    with chdir(build_dir):
        run("cmake ..", sudo=True)
        run(f"cmake --build . -j{get_threads_num()}", sudo=True)

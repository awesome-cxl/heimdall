import typer
from loguru import logger

import benchmark.basic_performance.scripts.utils.batch as batch
import benchmark.basic_performance.scripts.utils.build as build_all
import benchmark.basic_performance.scripts.utils.result as result
import benchmark.basic_performance.scripts.utils.utils as utils
from heimdall.utils.path import get_workspace_path

app = typer.Typer()


@app.command()
def build(config: str):
    logger.info("Build basic performance benchmarks")
    if config in ["bw"]:
        build_task("100")
    elif config in ["cache"]:
        build_task("200")
    elif config in ["all"]:
        build_task("100")
        build_task("200")
    else:
        raise Exception(f"this is the unknown task: {config}")


@app.command()
def run(config: str):
    logger.info("Run basic performance benchmarks")
    if config in ["bw"]:
        run_task("100")
    elif config in ["cache"]:
        run_task("200")
    elif config in ["all"]:
        run_task("100")
        run_task("200")
    else:
        raise Exception(f"this is the unknown task: {config}")


@app.command()
def install(config: str):
    logger.info("installing")
    raise Exception("Unimplemented")


@app.command
def plot(config: str):
    logger.info("plotting")
    raise Exception("Unimplemented")


@app.command()
def build_task(task_id: str):
    # file = utils.find_file_with_prefix(task_id)
    machine = utils.get_architecture()
    build_type = "release"
    # utils.check_task_continuous(file)
    build_all.build(machine, build_type, task_id)


@app.command()
def run_task(task_id: str):
    build_type = "release"
    machine = utils.get_architecture()
    output_path = utils.get_task_directory(task_id)
    file = utils.find_file_with_prefix(task_id)
    script_path = get_workspace_path() / "benchmark" / "basic_performance" / "scripts" / "batch" / f"{file}"
    batch.run_batch(script_path, build_type, output_path, machine, task_id)
    result.make_result(output_path, task_id)

import datetime

import typer
from loguru import logger

import benchmark.lockfree_bench.run_bench as run_bench

app = typer.Typer()


@app.command()
def build(config: str):
    logger.info("Building")
    logger.info(f"Config: {config}")
    run_bench.build()


@app.command()
def run(config: str):
    logger.info("Running")
    logger.info(f"Config: {config}")

    machine = config
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results = {}

    run_bench.run(machine, timestamp, results)
    if config != "basic":
        run_bench.plot(machine, timestamp)


@app.command()
def install(config: str):
    logger.info("Installing")
    run_bench.install_deps()


@app.command
def plot(config: str):
    logger.info("plotting")
    pass

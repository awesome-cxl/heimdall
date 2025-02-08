import typer
from loguru import logger

import benchmark.basic_performance.scripts.run as runner

app = typer.Typer()


@app.command()
def build(config: str):
    logger.info("basic perf build bench")
    if config in ["bw"]:
        runner.build("100")
    elif config in ["cache"]:
        runner.build("200")
    elif config in ["all"]:
        runner.build("100")
        runner.build("200")
    else:
        logger.error(f"this is the unknown task: {config}")
    pass


@app.command()
def run(config: str):
    logger.info("basic perf run bench")
    if config in ["bw"]:
        runner.run("100")
    elif config in ["cache"]:
        runner.run("200")
    elif config in ["all"]:
        runner.run("100")
        runner.run("200")
    else:
        logger.error(f"this is the unknown task: {config}")
    pass


@app.command()
def install(config: str):
    logger.info("installing")
    pass


@app.command
def plot(config: str):
    logger.info("plotting")
    pass

import typer
from loguru import logger

app = typer.Typer()


@app.command()
def build(config: str):
    logger.info("Building")
    logger.info(f"Config: {config}")
    pass


@app.command()
def run(config: str):
    logger.info("Running")
    logger.info(f"Config: {config}")
    pass


@app.command()
def install(config: str):
    logger.info("Installing")
    pass


@app.command
def plot(config: str):
    logger.info("plotting")
    pass

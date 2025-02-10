import typer
from invoke import UnexpectedExit
from loguru import logger

import benchmark.basic_performance.bench as basic_perf
import benchmark.llm_bench.bench as llm_bench

app = typer.Typer()


@app.command()
def build(bench_name: str, config: str):
    scripts = {"basic": basic_perf.build, "llm": llm_bench.build}

    if bench_name not in scripts:
        logger.error(f"Invalid benchmark name: {bench_name}")
        exit()

    bench = scripts[bench_name]
    logger.info(f"Building {bench_name} benchmark")
    bench(config)
    logger.success(f"Build {bench_name} benchmark successfully")


@app.command()
def run(bench_name: str, config: str):
    scripts = {"basic": basic_perf.run, "llm": llm_bench.run}

    if bench_name not in scripts:
        logger.error(f"Invalid benchmark name: {bench_name}")
        exit()

    bench = scripts[bench_name]
    logger.info(f"Running {bench_name} benchmark")
    bench(config)
    logger.success(f"Run {bench_name} benchmark successfully")


@app.command()
def all(bench_name: str, config: str):
    scripts = {"basic": basic_perf, "llm": llm_bench}

    if bench_name not in scripts:
        logger.error(f"Invalid benchmark name: {bench_name}")
        exit()

    bench = scripts[bench_name]
    logger.info(f"Running all {bench_name} benchmark")
    try:
        bench.install(config)
        bench.build(config)
        bench.run(config)
        bench.plot(config)
    except UnexpectedExit as e:
        logger.error(f"Error: {e}")
        exit()
    logger.success(f"Run all {bench_name} benchmark successfully")


@app.command()
def install(bench_name: str, config: str):
    scripts = {"basic": basic_perf.install, "llm": llm_bench.install}

    if bench_name not in scripts:
        logger.error(f"Invalid benchmark name: {bench_name}")
        exit()

    bench = scripts[bench_name]
    logger.info(f"Installing {bench_name} benchmark")
    bench(config)
    logger.success(f"Install {bench_name} benchmark successfully")
    pass


@app.command
def plot(bench_name: str, config: str):
    logger.info("plotting")
    scripts = {"basic": basic_perf.plot, "llm": llm_bench.plot}

    if bench_name not in scripts:
        logger.error(f"Invalid benchmark name: {bench_name}")
        exit()

    bench = scripts[bench_name]
    logger.info(f"Plotting {bench_name} benchmark")
    bench(config)
    logger.success(f"Plot {bench_name} benchmark successfully")
    pass


import typer

app = typer.Typer()

# find sub typers under behcnarmker/<sub-dir>/bench.py
# app.add_typer(basic_bench_app, name = "basic")

# `perf` as a python context manager
# from heimdall import perf
# with perf(perf_config):
#     bench.run(bench_config)

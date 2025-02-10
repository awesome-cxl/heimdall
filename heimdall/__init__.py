import typer

from benchmark.basic_performance import app as basic_perf_app
from heimdall.bench import app as bench_app
from heimdall.utils.path import app as path_app

app = typer.Typer()
app.add_typer(bench_app, name="bench")
app.add_typer(path_app, name="path")
app.add_typer(basic_perf_app, name="basic-performance")

if __name__ == "__main__":
    app()

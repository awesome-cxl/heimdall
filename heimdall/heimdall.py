import typer

from heimdall.bench import app as bench_app
from heimdall.utils.path import app as path_app

app = typer.Typer()
app.add_typer(bench_app, name="bench")
app.add_typer(path_app, name="path")

if __name__ == "__main__":
    app()

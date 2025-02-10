import typer

from benchmark.basic_performance.build import app as build_app

app = typer.Typer()
app.add_typer(build_app, name="build")

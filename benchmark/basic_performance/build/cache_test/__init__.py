import typer
from benchmark.basic_performance.build.cache_test.module import app as module_app

app = typer.Typer()
app.add_typer(module_app, name="module")

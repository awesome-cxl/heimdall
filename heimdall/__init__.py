import typer
from heimdall.bench import app as bench_app

app = typer.Typer()
app.add_typer(bench_app, name = "bench")

if __name__ == "__main__":
    app()
import typer

app = typer.Typer()


@app.command()
def build(config: str):
    pass


@app.command()
def run(config: str):
    pass

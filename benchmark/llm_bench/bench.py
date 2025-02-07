import typer
#from invoke import run, UnexpectedExit

app = typer.Typer()

@app.command()
def build(config: str):
    print("build llm bench")
    print(f"config:{config}")
    pass

@app.command()
def run(config: str):
    print("run llm bench")
    print(f"config:{config}")
    pass


@app.command()
def install(config: str):
    print("installing")
    pass


@app.command
def plot(config: str):
    print("plotting")
    pass

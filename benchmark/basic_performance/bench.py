import typer
import benchmark.basic_performance.scripts.run as runner

app = typer.Typer()

@app.command()
def build(config: str):
    print("basic perf build bench")
    if config in ["bw"]:
        runner.build("100")
    elif config in ["cache"]:
        runner.build("200")
    else:
        print(f"this is the unknown task: {config}")
    pass

@app.command()
def run(config: str):
    print("basic perf run bench")
    if config in ["bw"]:
        runner.run("100")
    elif config in ["cache"]:
        runner.run("200")
    else:
        print(f"this is the unknown task: {config}")
    pass


@app.command()
def install(config: str):
    print("installing")
    pass


@app.command
def plot(config: str):
    print("plotting")
    pass

import typer
from invoke import UnexpectedExit
import benchmark.basic_performance.bench as basic_perf
import benchmark.llm_bench.bench as llm_bench

app = typer.Typer()

@app.command()
def build(bench_name: str, config: str):
    print("im here")
    scripts = {
       "basic": basic_perf.build,
       "llm": llm_bench.build
    }
    
    if bench_name not in scripts:
        print(f"Invalid benchmark name: {bench_name}")
        raise typer.Exit()
    
    bench = scripts[bench_name]
    typer.echo(f"Building {bench_name} benchmark")
    bench(config)
    typer.echo(f"Build {bench_name} benchmark successfully")
    
@app.command()
def run(bench_name: str, config: str):
    scripts = {
       "basic": basic_perf.run,
       "llm": llm_bench.run   
    }
    
    if bench_name not in scripts:
        print(f"Invalid benchmark name: {bench_name}")
        raise typer.Exit()
    
    bench = scripts[bench_name]
    typer.echo(f"Running {bench_name} benchmark")
    bench(config)
    typer.echo(f"Run {bench_name} benchmark successfully")

@app.command()
def all(bench_name: str, config: str):
    scripts = {
       "basic": basic_perf,
       "llm": llm_bench   
    }
    
    if bench_name not in scripts:
        print(f"Invalid benchmark name: {bench_name}")
        raise typer.Exit()
    
    bench = scripts[bench_name]
    typer.echo(f"Running all {bench_name} benchmark")
    try:
        bench.build(config)
        bench.run(config)
    except UnexpectedExit as e:
        print(f"Error: {e}")
        raise typer.Exit()
    typer.echo(f"Run all {bench_name} benchmark successfully")


if __name__ == "__main__":
    app()
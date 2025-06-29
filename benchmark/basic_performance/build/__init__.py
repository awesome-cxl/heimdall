import typer
from benchmark.basic_performance.build.bw_latency_test import app as bw_lat_app
from benchmark.basic_performance.build.cache_test import app as cache_test_app

app = typer.Typer()
app.add_typer(bw_lat_app, name="bw-latency-test")
app.add_typer(cache_test_app, name="cache-test")

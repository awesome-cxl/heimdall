#
# MIT License
#
# Copyright (c) 2025 Jangseon Park
# Affiliation: University of California San Diego CSE
# Email: jap036@ucsd.edu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import typer

import benchmark.basic_performance.scripts.utils.batch as batch
import benchmark.basic_performance.scripts.utils.build as build_all
import benchmark.basic_performance.scripts.utils.result as result
import benchmark.basic_performance.scripts.utils.utils as utils
from heimdall.utils.path import get_workspace_path

app = typer.Typer()


@app.command()
def build(task_id: str):
    # file = utils.find_file_with_prefix(task_id)
    machine = utils.get_architecture()
    build_type = "release"
    # utils.check_task_continuous(file)
    build_all.build(machine, build_type, task_id)


@app.command()
def run(task_id: str):
    build_type = "release"
    machine = utils.get_architecture()
    output_path = utils.get_task_directory(task_id)
    file = utils.find_file_with_prefix(task_id)
    script_path = (
        get_workspace_path()
        / "benchmark"
        / "basic_performance"
        / "scripts"
        / "batch"
        / f"{file}"
    )
    batch.run_batch(script_path, build_type, output_path, machine, task_id)
    result.make_result(output_path, task_id)


if __name__ == "__main__":
    app()

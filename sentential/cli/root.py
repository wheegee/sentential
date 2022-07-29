import typer
from sentential.lib.shapes.aws import Runtimes
from sentential.lib.template import InitTime

root = typer.Typer()

@root.command()
def init(repository_name: str, runtime: Runtimes):
    """{repository}"""
    InitTime(repository_name).scaffold(f"public.ecr.aws/lambda/{runtime.value}:latest")
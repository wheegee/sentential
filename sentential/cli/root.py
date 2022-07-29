import typer
from sentential.lib.shapes.aws import Runtimes
from sentential.lib.template import InitTime
from sentential.lib.local import Image, Repository

root = typer.Typer()


@root.command()
def build(tag: str = "latest"):
    """{repository} with {tag}"""
    Image.build(tag)


@root.command()
def publish(tag: str = "latest"):
    """{repository} with {tag}"""
    Repository(Image(tag)).publish()


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """{repository}"""
    InitTime(repository_name).scaffold(f"public.ecr.aws/lambda/{runtime.value}:latest")

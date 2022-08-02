import typer
from sentential.lib.shapes.aws import Runtimes
from sentential.lib.template import InitTime
from sentential.lib.local import Image, Repository
from sentential.lib.facts import require_sntl_file

root = typer.Typer()


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """{repository}"""
    InitTime(repository_name).scaffold(f"public.ecr.aws/lambda/{runtime.value}:latest")

@root.command()
def build(tag: str = typer.Argument("latest", envvar="TAG")):
    """{repository} with {tag}"""
    require_sntl_file()
    Image.build(tag)


@root.command()
def publish(tag: str = typer.Argument("latest", envvar="TAG")):
    """{repository} with {tag}"""
    require_sntl_file()
    Repository(Image(tag)).publish()
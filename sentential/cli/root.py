import typer
from sentential.lib.shapes.aws import Runtimes
from sentential.lib.template import InitTime
from sentential.lib.local import Repository, Image
from sentential.lib.ontology import Ontology
from sentential.lib.clients import clients

root = typer.Typer()


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """initialize sentential project"""
    InitTime(repository_name).scaffold(f"public.ecr.aws/lambda/{runtime.value}:latest")


@root.command()
def build(tag: str = typer.Argument("latest", envvar="TAG")):
    """build lambda image"""
    Image.build(tag)


@root.command()
def publish(from_tag: str = typer.Argument("latest", envvar="TAG"), to_tag: str = None):
    """publish lambda image to aws"""
    if to_tag is None:
        to_tag = Ontology().next_build_semver()

    Repository().publish(Image.retag(from_tag, to_tag))


@root.command()
def ls():
    """show images"""
    Ontology().print()

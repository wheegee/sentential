from sentential.lib.const import CWI_TAG
from sentential.lib.shapes.aws import Runtimes
from sentential.lib.template import InitTime
from sentential.lib.local import Image, Repository
from sentential.lib.ontology import Ontology

import typer

root = typer.Typer()


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """initialize sentential project"""
    InitTime(repository_name).scaffold(f"public.ecr.aws/lambda/{runtime.value}:latest")


@root.command()
def build(tag: str = typer.Argument(CWI_TAG, envvar="CWI_TAG")):
    """build lambda image"""
    Image.build(tag)


@root.command()
def publish(
    from_tag: str = typer.Argument(CWI_TAG, envvar="CWI_TAG"),
    to_tag: str = typer.Argument(None, envvar="TAG"),
    major: bool = typer.Option(False),
    minor: bool = typer.Option(False),
):
    """publish lambda image to aws"""
    ontology = Ontology()

    if to_tag is None:
        to_tag = ontology.next(major, minor)

    image = Image(from_tag)

    if ontology.published(image.id):
        print(f"image {image.id} already published")
    else:
        Repository().publish(image.label_for_shipment(to_tag))


@root.command()
def ls():
    """show images"""
    Ontology().print()

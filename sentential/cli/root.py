from sentential.lib.const import CWI_TAG
from sentential.lib.shapes.aws import Runtimes
from sentential.lib.template import InitTime
from sentential.lib.local import Image, Repository
from sentential.lib.ontology import Ontology
from sentential.lib.clients import clients
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
def publish(from_tag: str = typer.Argument(CWI_TAG, envvar="CWI_TAG"), to_tag: str = typer.Argument(None, envvar="TAG")):
    """publish lambda image to aws"""
    ont = Ontology()

    if to_tag is None:
        to_tag = ont.next_build_semver()

    image = Image.retag(from_tag, to_tag)

    if ont.sha_exists(image.id):
        print(f"image {image.id} already exists")
    else:
        Repository().publish(image)


@root.command()
def ls():
    """show images"""
    Ontology().print()

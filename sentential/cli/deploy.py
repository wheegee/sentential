from sentential.lib.const import CWI_TAG
from sentential.lib.aws import Lambda as AwsLambda
from sentential.lib.aws import Image as AwsImage
from sentential.lib.local import Lambda as LocalLambda
from sentential.lib.local import Image as LocalImage
from sentential.lib.ontology import Ontology
import typer

deploy = typer.Typer()


@deploy.command()
def aws(
    tag: str = typer.Argument(None, envvar="TAG"),
    public_url: bool = typer.Option(False),
):
    """deploy lambda image to aws"""
    ontology = Ontology()

    if tag is None:
        tag = ontology.latest()

    AwsLambda(AwsImage(tag)).deploy(public_url)


@deploy.command()
def local(
    tag: str = typer.Argument(CWI_TAG, envvar="TAG"),
    public_url: bool = typer.Option(default=False),
):
    """build and deploy local lambda container"""
    LocalLambda(LocalImage(tag)).deploy(public_url)

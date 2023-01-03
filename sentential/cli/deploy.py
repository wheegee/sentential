import typer
from rich import print
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.mounts.local_lambda_public_url import LocalLambdaPublicUrlMount
from sentential.lib.mounts.aws_lambda_public_url import AwsLambdaPublicUrlMount
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import Architecture

deploy = typer.Typer()


@deploy.command()
def local(tag: str = typer.Argument(None), public_url: bool = typer.Option(False)):
    """deploy local lambda container"""
    ontology = Ontology()
    image = LocalImagesDriver(ontology).get_image(tag)
    print(LocalLambdaDriver(ontology).deploy(image))

    if public_url:
        LocalLambdaPublicUrlMount(ontology).mount()
    else:
        LocalLambdaPublicUrlMount(ontology).umount()


@deploy.command()
def aws(
    tag: str = typer.Argument(None),
    arch: Architecture = typer.Option(None),
    public_url: bool = typer.Option(False),
):
    """deploy lambda image to aws"""
    ontology = Ontology()
    image = AwsEcrDriver(ontology).get_image(tag)
    print(AwsLambdaDriver(ontology).deploy(image, arch))

    if public_url:
        AwsLambdaPublicUrlMount(ontology).mount()
    else:
        AwsLambdaPublicUrlMount(ontology).umount()

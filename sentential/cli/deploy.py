import typer
from rich import print
from sentential.lib.drivers.aws_lambda import AwsEcrDriver, AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import CURRENT_WORKING_IMAGE_TAG, Architecture
from sentential.lib.semver import SemVer

deploy = typer.Typer()


@deploy.command()
def local(
    tag: str = typer.Argument(CURRENT_WORKING_IMAGE_TAG, envvar="TAG"),
    arch: Architecture = typer.Option("amd64"),
):
    """build and deploy local lambda container"""
    ontology = Ontology()
    docker = LocalImagesDriver(ontology)
    ecr = AwsEcrDriver(ontology)
    func = LocalLambdaDriver(ontology)

    try:
        image = docker.image_by_tag(tag, arch.value)
    except:
        image = ecr.image_by_tag(tag, arch.value)
        docker.pull(image)

    print(func.deploy(image))


@deploy.command()
def aws(
    tag: str = typer.Argument(None, envvar="TAG"),
    arch: Architecture = typer.Option("amd64"),
):
    """deploy lambda image to aws"""
    ontology = Ontology()
    ecr = AwsEcrDriver(ontology)
    func = AwsLambdaDriver(ontology)

    if tag is None:
        tag = SemVer(ecr.images()).latest

    image = ecr.image_by_tag(tag, arch.value)
    print(func.deploy(image))

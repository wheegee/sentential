import typer
from rich import print
from sentential.lib.drivers.aws_lambda import AwsEcrDriver, AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import CURRENT_WORKING_IMAGE_TAG
from sentential.lib.semver import SemVer

deploy = typer.Typer()


@deploy.command()
def local(
    tag: str = typer.Argument(CURRENT_WORKING_IMAGE_TAG, envvar="TAG"),
):
    """build and deploy local lambda container"""
    ontology = Ontology()
    docker = LocalImagesDriver(ontology)
    ecr = AwsEcrDriver(ontology)
    func = LocalLambdaDriver(ontology)
    try:
        image = docker.image_by_tag(tag)
    except:
        image = ecr.image_by_tag(tag)
        docker.pull(image)

    print(func.deploy(image))


@deploy.command()
def aws(
    tag: str = typer.Argument(None, envvar="TAG"),
):
    """deploy lambda image to aws"""
    ontology = Ontology()
    ecr = AwsEcrDriver(ontology)
    func = AwsLambdaDriver(ontology)
    if tag is None:
        tag = SemVer(ecr.images()).latest
        
    image = ecr.image_by_tag(tag)
    print(func.deploy(image))

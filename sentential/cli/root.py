import typer
from sentential.lib.clients import clients
from sentential.lib.template import Init
from sentential.lib.shapes import Runtimes
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.semver import SemVer
from sentential.lib.ontology import Ontology
from sentential.lib.joinery import Joinery
from sentential.lib.shapes import CURRENT_WORKING_IMAGE_TAG

from rich import print

root = typer.Typer()


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """initialize sentential project"""
    aws_supported_image = f"public.ecr.aws/lambda/{runtime.value}:latest"
    Init(repository_name, aws_supported_image).scaffold()


@root.command()
def build():
    """build lambda image"""
    local = LocalLambdaDriver(Ontology())
    print(local.build(CURRENT_WORKING_IMAGE_TAG))


@root.command()
def publish(major: bool = typer.Option(False), minor: bool = typer.Option(False)):
    """publish lambda image"""
    ontology = Ontology()
    aws = AwsLambdaDriver(ontology)
    local = LocalLambdaDriver(ontology)
    version = SemVer(aws.images()).next(major, minor)
    print(local.publish(CURRENT_WORKING_IMAGE_TAG, version))


@root.command()
def login():
    """login to ecr"""
    clients.docker.login_ecr()


@root.command()
def ls():
    """list image information"""
    print(Joinery(Ontology()).list(["tags"]))


@root.command()
def clean(remote: bool = typer.Option(False)):
    """clean images"""
    ontology = Ontology()
    aws = AwsLambdaDriver(ontology)
    local = LocalLambdaDriver(ontology)

    for image in local.images():
        clients.docker.image.remove(image.id, force=True)

    if remote:
        images = []
        for image in aws.images():
            images.append({"imageDigest": image.digest})

        clients.ecr.batch_delete_image(
            repositoryName=ontology.context.repository_name, imageIds=images
        )

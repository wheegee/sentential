import typer
from sentential.lib.clients import clients
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.template import Init
from sentential.lib.shapes import Runtimes
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
    docker = LocalImagesDriver(Ontology())
    print(docker.build(CURRENT_WORKING_IMAGE_TAG))


@root.command()
def publish(major: bool = typer.Option(False), minor: bool = typer.Option(False)):
    """publish lambda image"""
    ontology = Ontology()
    ecr = AwsEcrDriver(ontology)
    docker = LocalImagesDriver(ontology)
    tag = SemVer(ecr.images()).next(major, minor)
    print(docker.push(tag))


@root.command()
def login():
    """login to ecr"""
    clients.docker.login_ecr()


@root.command()
def ls():
    """list image information"""
    print(Joinery(Ontology()).list(["tags", "uri"]))


@root.command()
def clean(remote: bool = typer.Option(False)):
    """clean images"""
    ontology = Ontology()
    LocalImagesDriver(ontology).clean()
    if remote:
        AwsEcrDriver(ontology).clean()


# @root.command()
# def wut(platform: typer.Option(None, )):
#     platforms = LocalImagesDriver(Ontology())._buildx_platforms()

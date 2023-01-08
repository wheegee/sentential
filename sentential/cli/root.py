from typing import List, Optional
import typer
from sentential.lib.clients import clients
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.template import Init
from sentential.lib.shapes import Architecture, Runtimes
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
def build(arch: Architecture = typer.Option(Architecture.system().value)):
    """build lambda image"""
    LocalImagesDriver(Ontology()).build(arch)


@root.command()
def publish(
    major: bool = typer.Option(False),
    minor: bool = typer.Option(False),
    arch: List[Architecture] = typer.Option([Architecture.system().value]),
    multiarch: bool = typer.Option(False),
):
    """publish lambda image"""
    ontology = Ontology()
    tag = AwsEcrDriver(ontology).next(major, minor)
    docker = LocalImagesDriver(ontology)

    if multiarch:
        docker.publish(tag, [a for a in Architecture])
    else:
        docker.publish(tag, [a for a in arch])


@root.command()
def login():
    """login to ecr"""
    clients.docker.login_ecr()


@root.command()
def ls():
    """list image information"""
    print(Joinery(Ontology()).list())


@root.command()
def clean(remote: bool = typer.Option(False)):
    """clean images"""
    ontology = Ontology()
    LocalImagesDriver(ontology).clean()
    if remote:
        AwsEcrDriver(ontology).clean()

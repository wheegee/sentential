from typing import List, Optional
import typer
from sentential.lib.clients import clients
from sentential.lib.drivers.local_images import LocalImagesDriver
from sentential.lib.drivers.aws_ecr import AwsEcrDriver
from sentential.lib.template import Init
from sentential.lib.shapes import Architecture, Runtimes
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
def build(arch: Architecture = typer.Option(None)):
    """build lambda image"""
    ontology = Ontology()
    docker = LocalImagesDriver(ontology)

    if arch:
        docker.build(arch.value)
    else:
        docker.build(Architecture.system().value)


@root.command()
def publish(
    major: bool = typer.Option(False),
    minor: bool = typer.Option(False),
    arch: List[Architecture] = typer.Option([]),
    multiarch: bool = typer.Option(False),
):
    """publish lambda image"""
    ontology = Ontology()
    ecr = AwsEcrDriver(ontology)
    docker = LocalImagesDriver(ontology)
    tag = SemVer(ecr.images()).next(major, minor)

    if multiarch:
        docker.publish(tag, [a.value for a in Architecture])
    elif arch:
        docker.publish(tag, [a.value for a in arch])
    else:
        docker.publish(tag, [Architecture.system().value])


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

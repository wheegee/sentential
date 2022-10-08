import typer
from sentential.lib.clients import clients
from sentential.lib.template import Init
from sentential.lib.shapes import Runtimes
from sentential.lib.drivers.local import LocalDriver
from sentential.lib.ontology import Ontology
from sentential.lib.joinery import Joinery
from rich import print

root = typer.Typer()


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """initialize sentential project"""
    aws_supported_image = f"public.ecr.aws/lambda/{runtime.value}:latest"
    Init(repository_name, aws_supported_image).scaffold()


@root.command()
def build(version: str = typer.Argument("latest", envvar="VERSION")):
    """build lambda image"""
    local = LocalDriver(Ontology())
    print(local.build(version))


@root.command()
def publish(version: str = typer.Argument("latest", envvar="VERSION")):
    """publish lambda image"""
    local = LocalDriver(Ontology())
    print(local.publish(version))


@root.command()
def login():
    """login to ecr"""
    clients.docker.login_ecr()


@root.command()
def ls():
    """list image information"""
    print(Joinery(Ontology()).list(["tags"]))

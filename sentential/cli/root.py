import typer
from sentential.lib.clients import clients
from sentential.lib.template import Init
from sentential.lib.shapes import Runtimes
from sentential.lib.drivers.local import LocalDriver
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.aws import AwsDriver
root = typer.Typer()


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """initialize sentential project"""
    Init(repository_name, runtime.value).scaffold()


@root.command()
def build(tag: str = typer.Argument("latest", envvar="CWI_TAG")):
    """build lambda image"""
    print(LocalDriver(Ontology()).build(tag))

@root.command()
def wut():
    AwsDriver(Ontology()).images()

@root.command()
def login():
    clients.docker.login_ecr()
    
# @root.command()
# def publish(
#     from_tag: str = typer.Argument("latest", envvar="CWI_TAG"),
#     to_tag: str = typer.Argument(None, envvar="TAG"),
#     major: bool = typer.Option(False),
#     minor: bool = typer.Option(False),
# ):
#     """publish lambda image to aws"""
#     pass


# @root.command()
# def ls():
#     """show images"""
#     pass

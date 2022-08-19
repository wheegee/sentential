import typer
from sentential.lib.aws import Image, Lambda, Repository
from rich.console import Console
from rich.table import Table
from rich import print
from sentential.lib.clients import clients

aws = typer.Typer()


@aws.command()
def deploy(
    tag: str = typer.Argument("latest", envvar="TAG"),
    public_url: bool = typer.Option(False),
):
    """deploy lambda image to aws"""
    Lambda(Image(tag)).deploy(public_url)


@aws.command()
def destroy(
    tag: str = typer.Argument("latest", envvar="TAG"),
):
    """destroy lambda deployment in aws"""
    Lambda(Image(tag)).destroy()


@aws.command()
def list():
    """list local lambda images"""
    table = Table("Tag", "Arch", "Deployed", "Sha")
    deployed = Lambda.deployed()
    for image in Repository().images():
        if deployed is not None and deployed.image.id == image.id:
            table.add_row(image.tag, image.arch, "True", image.id)
        else:
            table.add_row(image.tag, image.arch, "False", image.id)

    print(table)


@aws.command()
def logs(follow: bool = typer.Option(False)):
    """dump running container logs"""
    Lambda.deployed().logs(follow)

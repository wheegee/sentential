import typer
from sentential.lib.local import Image, Lambda, Repository
from rich.console import Console
from rich.table import Table
from rich import print

local = typer.Typer()


@local.command()
def deploy(
    tag: str = typer.Argument("latest", envvar="TAG"),
    public_url: bool = typer.Option(default=False),
):
    """build and deploy local lambda container"""
    Lambda(Image(tag)).deploy(public_url)


@local.command()
def destroy(
    tag: str = typer.Argument("latest", envvar="TAG"),
):
    """destroy local lambda container"""
    Lambda(Image(tag)).destroy()


@local.command()
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


@local.command()
def logs(follow: bool = typer.Option(False)):
    """dump running container logs"""
    Lambda.deployed().logs(follow)

import typer
from sentential.lib.local import Image, Lambda, Repository
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich import print
from sentential.lib.clients import clients

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
    console = Console()
    table = Table("Tag", "Arch")
    for image in Repository().images():
        table.add_row(image.tag, image.arch())
    print(table)


@local.command()
def logs(follow: bool = typer.Option(False)):
    """dump running container logs"""
    # This initialization implies Image should be a method argument, not a class initializer
    Lambda(Image("latest")).logs(follow)

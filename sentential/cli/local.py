import typer
from sentential.lib.local import Image, Lambda, Repository
from rich.console import Console
from rich.table import Table

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
def show():
    console = Console() 
    table = Table("Tag", "Arch")
    for image in Repository().images():
        table.add_row(image.tag, image.arch())
    console.print(table)
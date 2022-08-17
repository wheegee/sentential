import typer
from sentential.lib.aws import Image, Lambda, Repository
from rich.console import Console
from rich.table import Table

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
def show():
    console = Console()
    table = Table("Tag", "Arch")
    for image in Repository().images():
        table.add_row(image.tag, image.arch())
    console.print(table)

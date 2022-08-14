import typer
from sentential.lib.local import Repository, Image, Lambda

local = typer.Typer()


@local.command()
def deploy(
    tag: str = typer.Argument("latest", envvar="TAG"),
    gateway: bool = typer.Option(default=True),
):
    Lambda(Image(tag)).deploy(gateway)


@local.command()
def destroy(
    tag: str = typer.Argument("latest", envvar="TAG"),
):
    Lambda(Image(tag)).destroy()

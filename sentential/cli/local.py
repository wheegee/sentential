import typer
from sentential.lib.local import Repository, Image, Lambda

local = typer.Typer()


@local.command()
def deploy(tag: str = "latest"):
    Lambda(Image(tag)).deploy()


@local.command()
def destroy(tag: str = "latest"):
    Lambda(Image(tag)).destroy()

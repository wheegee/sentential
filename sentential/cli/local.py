import typer
from sentential.lib.local import Repository, Image, Lambda
local = typer.Typer()

@local.command()
def build(tag: str = "latest"):
    Image.build(tag)

@local.command()
def deploy(tag: str = "latest"):
    Lambda(Image(tag)).deploy()

@local.command()
def destroy(tag: str = "latest"):
    Lambda(Image(tag)).destroy()

@local.command()
def publish(tag: str = "latest"):
    Lambda(Image(tag)).publish()
import typer
from sentential.lib.aws import Repository, Image, Lambda
aws = typer.Typer()

@aws.command()
def deploy(tag: str = "latest"):
    Lambda(Image(tag)).deploy()

@aws.command()
def destroy(tag: str = "latest"):
    Lambda(Image(tag)).destroy()

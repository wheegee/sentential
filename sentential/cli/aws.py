import typer
from sentential.lib.aws import Image, Lambda, Repository
import polars as pl

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
    """list aws lambda images"""
    print(Repository().df())


@aws.command()
def logs(follow: bool = typer.Option(False)):
    """dump running container logs"""
    Lambda.deployed().logs(follow)

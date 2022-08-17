import typer
from sentential.lib.aws import Image, Lambda

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

import typer
from sentential.lib.aws import Image, Lambda

aws = typer.Typer()


@aws.command()
def deploy(
    tag: str = typer.Argument("latest", envvar="TAG"),
    gateway: bool = typer.Option(True),
):
    Lambda(Image(tag)).deploy(gateway)


@aws.command()
def destroy(
    tag: str = typer.Argument("latest", envvar="TAG"),
):
    Lambda(Image(tag)).destroy()

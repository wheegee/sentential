import typer
from sentential.lib.aws import Image, Lambda
from sentential.lib.facts import Partitions

aws = typer.Typer()


@aws.command()
def deploy(
    tag: str = typer.Argument("latest", envvar="TAG"),
    partition: Partitions = typer.Argument(
        Partitions.default.value, envvar="PARTITION"
    ),
    gateway: bool = typer.Option(True),
):
    Lambda(Image(tag), partition.value).deploy(gateway)


@aws.command()
def destroy(
    tag: str = typer.Argument("latest", envvar="TAG"),
    partition: Partitions = typer.Argument(
        Partitions.default.value, envvar="PARTITION"
    ),
):
    Lambda(Image(tag), partition.value).destroy()

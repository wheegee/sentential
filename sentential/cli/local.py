import typer
from sentential.lib.local import Repository, Image, Lambda
from sentential.lib.facts import Partitions

local = typer.Typer()


@local.command()
def deploy(
    tag: str = typer.Argument("latest", envvar="TAG"),
    partition: Partitions = typer.Argument(
        Partitions.default.value, envvar="PARTITION"
    ),
    gateway: bool = typer.Option(default=True),
):
    Lambda(Image(tag), partition.value).deploy(gateway)


@local.command()
def destroy(
    tag: str = typer.Argument("latest", envvar="TAG"),
    partition: Partitions = typer.Argument(
        Partitions.default.value, envvar="PARTITION"
    ),
):
    Lambda(Image(tag), partition.value).destroy()

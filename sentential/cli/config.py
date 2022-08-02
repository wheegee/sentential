import typer
from sentential.lib.store import ConfigStore
from sentential.lib.facts import Partitions

config = typer.Typer()


@config.command()
def read(
    partition: Partitions = typer.Argument(Partitions.default.value, envvar="PARTITION")
):
    """config for {repository} lambda"""
    ConfigStore(partition.value).read()


@config.command()
def write(
    key: str,
    value: str,
    partition: Partitions = typer.Argument(
        Partitions.default.value, envvar="PARTITION"
    ),
):
    """config for {repository} lambda"""
    ConfigStore(partition.value).write(key, value)


@config.command()
def delete(
    key: str,
    partition: Partitions = typer.Argument(
        Partitions.default.value, envvar="PARTITION"
    ),
):
    """config for {repository} lambda"""
    ConfigStore(partition.value).delete(key)

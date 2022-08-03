import typer
from sentential.lib.store import SecretStore
from sentential.lib.facts import Partitions

secret = typer.Typer()


@secret.command()
def read(
    partition: Partitions = typer.Argument(Partitions.default.value, envvar="PARTITION")
):
    """secrets for {repository} lambda"""
    SecretStore(partition.value).read()


@secret.command()
def write(
    key: str,
    value: str,
    partition: Partitions = typer.Argument(
        Partitions.default.value, envvar="PARTITION"
    ),
):
    """secrets for {repository} lambda"""
    SecretStore(partition.value).write(key, value)


@secret.command()
def delete(
    key: str,
    partition: Partitions = typer.Argument(
        Partitions.default.value, envvar="PARTITION"
    ),
):
    """secrets for {repository} lambda"""
    SecretStore(partition.value).delete(key)

import typer
from sentential.lib.store import ConfigStore

config = typer.Typer()


@config.command()
def read():
    """config for {repository} lambda"""
    ConfigStore().read()


@config.command()
def write(key: str, value: str):
    """config for {repository} lambda"""
    ConfigStore().write(key, value)


@config.command()
def delete(key: str):
    """config for {repository} lambda"""
    ConfigStore().delete(key)

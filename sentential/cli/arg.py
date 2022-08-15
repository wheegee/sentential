import typer
from sentential.lib.store import Arg

arg = typer.Typer()


@arg.command()
def read():
    """config for {repository} lambda"""
    Arg().read()


@arg.command()
def write(key: str, value: str):
    """config for {repository} lambda"""
    Arg().write(key, value)


@arg.command()
def delete(key: str):
    """config for {repository} lambda"""
    Arg().delete(key)

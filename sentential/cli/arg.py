import typer
from sentential.lib.store import Arg

arg = typer.Typer()


@arg.command()
def read():
    """read build args for lambda"""
    Arg().read()


@arg.command()
def write(key: str, value: str):
    """write build arg for lambda"""
    Arg().write(key, value)


@arg.command()
def delete(key: str):
    """delete build arg for lambda"""
    Arg().delete(key)

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
    if len(value) > 1:
        Arg().write(key, value)
    else:
        Arg().write(key, value[0])


@arg.command()
def delete(key: str):
    """delete build arg for lambda"""
    Arg().delete(key)


@arg.command()
def clear():
    """delete all args"""
    Arg().clear()

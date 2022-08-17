import typer
from sentential.lib.store import Env

env = typer.Typer()


@env.command()
def read():
    """read runtime environment variables for lambda"""
    Env().read()


@env.command()
def write(key: str, value: str):
    """write runtime environment variable for lambda"""
    Env().write(key, value)


@env.command()
def delete(key: str):
    """delete runtime environment variable for lambda"""
    Env().delete(key)

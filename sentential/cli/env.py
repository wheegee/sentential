import typer
from sentential.lib.store import Env

env = typer.Typer()


@env.command()
def read():
    """config for {repository} lambda"""
    Env().read()


@env.command()
def write(key: str, value: str):
    """config for {repository} lambda"""
    Env().write(key, value)


@env.command()
def delete(key: str):
    """config for {repository} lambda"""
    Env().delete(key)

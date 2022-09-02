import typer
from typing import List
from sentential.lib.store import Env

env = typer.Typer()


@env.command()
def read():
    """read runtime environment variables for lambda"""
    Env().read()


@env.command()
def write(key: str, value: List[str]):
    """write runtime environment variable for lambda"""
    if len(value) > 1:
        Env().write(key, value)
    else:
        Env().write(key, value[0])


@env.command()
def delete(key: str):
    """delete runtime environment variable for lambda"""
    Env().delete(key)


@env.command()
def clear():
    """delete all env"""
    Env().clear()

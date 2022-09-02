from typing import List
import typer
from sentential.lib.store import Provision

config = typer.Typer()


@config.command()
def read():
    """read lambda provisioning config"""
    Provision().read()


@config.command()
def write(key: str, value: List[str]):
    """write lambda provisioning config"""
    if len(value) > 1:
        Provision().write(key, value)
    else:
        Provision().write(key, value[0])


@config.command()
def delete(key: str):
    """delete lambda provisioning config"""
    Provision().delete(key)


@config.command()
def clear():
    """delete all config"""
    Provision().clear()

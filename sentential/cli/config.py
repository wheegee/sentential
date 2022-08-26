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
    Provision().write(key, value)


@config.command()
def delete(key: str):
    """delete lambda provisioning config"""
    Provision().delete(key)

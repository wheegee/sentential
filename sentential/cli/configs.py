import typer
from typing import List
from rich import print
from sentential.lib.ontology import Ontology

configs = typer.Typer()


@configs.command()
def read() -> None:
    f"""read provisioning configs for lambda"""
    print(Ontology().configs.read())


@configs.command()
def write(key: str, value: List[str]):
    f"""write provisioning configs for lambda"""
    Ontology().configs.write(key, value)


@configs.command()
def delete(key: str):
    f"""delete provisioning configs for lambda"""
    Ontology().configs.delete(key)


@configs.command()
def clear():
    f"""delete all provisioning configs for lambda"""
    Ontology().configs.clear()

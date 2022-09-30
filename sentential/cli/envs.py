import typer
from typing import List
from rich import print
from sentential.lib.ontology import Ontology

envs = typer.Typer()


@envs.command()
def read() -> None:
    f"""read environment variables for lambda"""
    print(Ontology().envs.read())


@envs.command()
def write(key: str, value: List[str]):
    f"""write environment variables for lambda"""
    Ontology().envs.write(key, value)


@envs.command()
def delete(key: str):
    f"""delete environment variables for lambda"""
    Ontology().envs.delete(key)


@envs.command()
def clear():
    f"""delete all environment variables for lambda"""
    Ontology().envs.clear()

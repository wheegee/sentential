import typer
from typing import List
from rich import print
from sentential.lib.ontology import Ontology

args = typer.Typer()


@args.command()
def read() -> None:
    f"""read build arguments for lambda"""
    print(Ontology().args.read())


@args.command()
def write(key: str, value: List[str]):
    f"""write build arguments for lambda"""
    Ontology().args.write(key, value)


@args.command()
def delete(key: str):
    f"""delete build arguments for lambda"""
    Ontology().args.delete(key)


@args.command()
def clear():
    f"""delete all build arguments for lambda"""
    Ontology().args.clear()

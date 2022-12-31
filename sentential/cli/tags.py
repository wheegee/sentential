import typer
from typing import List
from rich import print
from sentential.lib.ontology import Ontology

tags = typer.Typer()


@tags.command()
def read() -> None:
    f"""read tags for resources"""
    print(Ontology().tags.read())


@tags.command()
def write(key: str, value: List[str]):
    f"""write tags for resources"""
    Ontology().tags.write(key, value)


@tags.command()
def delete(key: str):
    f"""delete tags for resources"""
    Ontology().tags.delete(key)


@tags.command()
def clear():
    f"""delete all resource tags"""
    Ontology().envs.clear()

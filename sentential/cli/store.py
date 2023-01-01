import typer
from typing import List
from rich import print
from sentential.lib.ontology import Ontology

store = typer.Typer()


@store.callback()
def namespace(ctx: typer.Context):
    ctx.obj = getattr(Ontology(), str(ctx.command.name))


@store.command()
def read(ctx: typer.Context) -> None:
    print(getattr(ctx.obj, str(ctx.command.name))())


@store.command()
def write(ctx: typer.Context, key: str, value: List[str]):
    getattr(ctx.obj, str(ctx.command.name))(key, value)


@store.command()
def delete(ctx: typer.Context, key: str):
    getattr(ctx.obj, str(ctx.command.name))(key)


@store.command()
def clear(ctx: typer.Context):
    getattr(ctx.obj, str(ctx.command.name))()

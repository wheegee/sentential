import typer
from typing import List
from rich import print
from sentential.lib.ontology import Ontology

store = typer.Typer()


@store.callback()
def namespace(ctx: typer.Context):
    ctx.obj = getattr(Ontology(), str(ctx.command.name))


@store.command()
def ls(ctx: typer.Context):
    """list store"""
    print(getattr(ctx.obj, str(ctx.command.name))())


@store.command()
def set(ctx: typer.Context, key: str, value: str):
    """set KEY VALUE in store"""
    print(getattr(ctx.obj, str(ctx.command.name))(key, value))


@store.command()
def rm(ctx: typer.Context, key: str):
    """delete KEY in store"""
    print(getattr(ctx.obj, str(ctx.command.name))(key))


@store.command()
def clear(ctx: typer.Context):
    """delete all in store"""
    print(getattr(ctx.obj, str(ctx.command.name))())

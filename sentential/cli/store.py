import typer
from rich import print
from typing import List, Tuple, Callable
from sentential.lib.store import Store
from sentential.lib.ontology import Ontology

store = typer.Typer()


def _from_context(ctx: typer.Context) -> Tuple[Store, Callable]:
    zero_arg, store, method, *n_arg = ctx.command_path.split(" ")
    store = getattr(Ontology(), store)
    method = getattr(store, method)
    return (store, method)


@store.command()
def ls(ctx: typer.Context):
    """list store"""
    store, method = _from_context(ctx)
    print(method())


@store.command()
def set(ctx: typer.Context, key: str, value: str):
    """set KEY VALUE in store"""
    store, method = _from_context(ctx)
    print(method(key, value))


@store.command()
def rm(ctx: typer.Context, key: str):
    """delete KEY in store"""
    store, method = _from_context(ctx)
    print(method(key))


@store.command()
def clear(ctx: typer.Context):
    """delete all in store"""
    store, method = _from_context(ctx)
    print(method())

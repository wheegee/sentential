import typer
from rich import print
from sentential.lib.template import Policy
from sentential.lib.ontology import Ontology


policy = typer.Typer()


@policy.command()
def cat():
    """render policy.json to console"""
    print(Policy(Ontology()).render())


@policy.command()
def ls():
    """show all available interpolations and values"""
    print(Policy(Ontology()).available_data())

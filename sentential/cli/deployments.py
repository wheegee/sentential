import typer
from sentential.lib.joinery import Joinery
from sentential.lib.ontology import Ontology
from rich import print

deployments = typer.Typer()


@deployments.command()
def all():
    print(Joinery(Ontology()).deployments())

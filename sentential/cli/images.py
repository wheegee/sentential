import typer
from sentential.lib.joinery import Joinery
from sentential.lib.ontology import Ontology
from rich import print

images = typer.Typer()

@images.command()
def local():
    print(Joinery(Ontology()).local_images())

@images.command()
def aws():
    print(Joinery(Ontology()).aws_images())
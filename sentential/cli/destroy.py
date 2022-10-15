import typer
from sentential.lib.drivers.local import LocalDriver
from sentential.lib.drivers.aws import AwsDriver
from sentential.lib.ontology import Ontology

destroy = typer.Typer()


@destroy.command()
def local():
    """destroy lambda deployment in aws"""
    local = LocalDriver(Ontology())
    local.destroy()


@destroy.command()
def aws():
    """destroy lambda deployment in aws"""
    aws = AwsDriver(Ontology())
    aws.destroy()

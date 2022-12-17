import typer
from rich import print
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver

invoke = typer.Typer()


@invoke.command()
def local(event: str):
    """build and deploy local lambda container"""
    ontology = Ontology()
    local = LocalLambdaDriver(ontology)
    print(local.invoke(event))


@invoke.command()
def aws(event: str):
    """deploy lambda image to aws"""
    ontology = Ontology()
    aws = AwsLambdaDriver(ontology)
    print(aws.invoke(event))

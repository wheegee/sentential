import typer
from sentential.lib.ontology import Ontology
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver

invoke = typer.Typer()


@invoke.command()
def local(event: str):
    """build and deploy local lambda container"""
    print(LocalLambdaDriver(Ontology()).invoke(event))


@invoke.command()
def aws(event: str):
    """deploy lambda image to aws"""
    print(AwsLambdaDriver(Ontology()).invoke(event))

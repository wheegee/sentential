import typer
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.aws_api_gateway import AwsApiGatewayDriver
from sentential.lib.ontology import Ontology

destroy = typer.Typer()


@destroy.command()
def local():
    """destroy lambda deployment in aws"""
    local = LocalLambdaDriver(Ontology())
    local.destroy()


@destroy.command()
def aws():
    """destroy lambda deployment in aws"""
    ontology = Ontology()
    aws_function = AwsLambdaDriver(ontology)
    deployed = aws_function.deployed()
    aws_function.destroy(deployed)

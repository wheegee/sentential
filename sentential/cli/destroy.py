import typer
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.mounts.local_lambda_public_url import LocalLambdaPublicUrlMount
from sentential.lib.ontology import Ontology

destroy = typer.Typer()


@destroy.command()
def local():
    """destroy lambda deployment in aws"""
    ontology = Ontology()
    local = LocalLambdaDriver(ontology)
    gw = LocalLambdaPublicUrlMount(ontology)
    local.destroy()


@destroy.command()
def aws():
    """destroy lambda deployment in aws"""
    ontology = Ontology()
    aws_function = AwsLambdaDriver(ontology)
    aws_function.destroy()

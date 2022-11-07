import typer
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.aws_api_gateway import AwsApiGatewayDriver
from sentential.lib.ontology import Ontology

trigger = typer.Typer()


@trigger.command()
def mount(
    path: str = typer.Argument(..., autocompletion=AwsApiGatewayDriver.autocomplete)
):
    """mount a thing"""
    ontology = Ontology()
    deployed = AwsLambdaDriver(ontology).deployed()
    api_gw = AwsApiGatewayDriver(ontology)
    api_gw.mount(path, deployed)


@trigger.command()
def umount():
    """unmount a thing"""
    ontology = Ontology()
    deployed = AwsLambdaDriver(ontology).deployed()
    api_gw = AwsApiGatewayDriver(ontology)
    api_gw.umount(deployed)


@trigger.command()
def ls():
    ontology = Ontology()
    deployed = AwsLambdaDriver(ontology).deployed()
    api_gw = AwsApiGatewayDriver(ontology)
    print(api_gw.ls(deployed))

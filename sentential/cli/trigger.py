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
    AwsApiGatewayDriver(ontology, deployed).mount(path)


@trigger.command()
def umount(
    all: bool = typer.Option(False),
    path: str = typer.Argument(None, autocompletion=AwsApiGatewayDriver.autocomplete),
):
    """unmount a thing"""
    ontology = Ontology()
    deployed = AwsLambdaDriver(ontology).deployed()
    gw = AwsApiGatewayDriver(ontology, deployed)
    if all:
        gw.umount("ALL")
    else:
        gw.umount(path)


@trigger.command()
def mounts():
    ontology = Ontology()
    deployed = AwsLambdaDriver(ontology).deployed()
    triggers = AwsApiGatewayDriver(ontology, deployed)
    print(triggers.mounts())

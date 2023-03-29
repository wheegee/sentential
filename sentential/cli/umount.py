import typer
from rich import print
from sentential.lib.mounts.aws_event_schedule import AwsEventScheduleMount
from sentential.lib.mounts.aws_api_gateway import AwsApiGatewayMount
from sentential.lib.ontology import Ontology

umount = typer.Typer()


@umount.command()
def schedule():
    """unmount lambda image from schedule"""
    AwsEventScheduleMount(Ontology()).umount()


@umount.command()
def route(
    path: str = typer.Argument(None, autocompletion=AwsApiGatewayMount.autocomplete)
):
    """unmount lambda image from api gateway"""
    for msg in AwsApiGatewayMount(Ontology()).umount():
        print(msg)

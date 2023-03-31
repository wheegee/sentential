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
    all: bool = typer.Option(
        False, "-a", "--all", help="unmount all routes integrated with lambda"
    ),
    path: str = typer.Argument(
        None,
        autocompletion=AwsApiGatewayMount.autocomplete,
        help="unmount lambda from given path",
    ),
):
    """unmount lambda image from api gateway"""
    if not all and path is None:
        print("you must provide either an explicit path or --all")
        exit(1)

    for msg in AwsApiGatewayMount(Ontology()).umount(path):
        print(msg)

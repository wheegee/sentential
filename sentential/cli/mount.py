import typer
from rich import print
from sentential.lib.mounts.aws_event_schedule import AwsEventScheduleMount
from sentential.lib.mounts.aws_api_gateway import AwsApiGatewayMount
from sentential.lib.ontology import Ontology

mount = typer.Typer()


@mount.command()
def schedule(
    schedule: str = typer.Argument(
        ..., help='"<Minutes> <Hours> <Day-of-month> <Month> <Day-of-week> <Year>"'
    ),
    payload: str = typer.Option("{}", help="lambda json payload"),
):
    """mount lambda image to schedule"""
    print(AwsEventScheduleMount(Ontology()).mount(schedule, payload))


@mount.command()
def route(
    path: str = typer.Argument(
        None,
        autocompletion=AwsApiGatewayMount.autocomplete,
        help="mount lambda to given path",
    )
):
    """mount lambda image to api gateway"""
    print(AwsApiGatewayMount(Ontology()).mount(path))

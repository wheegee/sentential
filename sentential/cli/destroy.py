import typer
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.mounts.aws_event_schedule import AwsEventScheduleMount
from sentential.lib.mounts.aws_api_gateway import AwsApiGatewayMount
from sentential.lib.ontology import Ontology

destroy = typer.Typer()


@destroy.command()
def local():
    """destroy lambda deployment in aws"""
    LocalLambdaDriver(Ontology()).destroy()


@destroy.command()
def aws():
    """destroy lambda deployment in aws"""
    AwsEventScheduleMount(Ontology()).umount()
    AwsApiGatewayMount(Ontology()).umount()
    AwsLambdaDriver(Ontology()).destroy()

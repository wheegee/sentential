import typer
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.ontology import Ontology

logs = typer.Typer()


@logs.command()
def local(follow: bool = typer.Option(False)):
    """dump running container logs"""
    local = LocalLambdaDriver(Ontology())
    local.logs(follow)


@logs.command()
def aws(follow: bool = typer.Option(False)):
    """dump running container logs"""
    aws = AwsLambdaDriver(Ontology())
    aws.logs(follow)

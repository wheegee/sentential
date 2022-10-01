import typer
from sentential.lib.drivers.aws import AwsDriver
from sentential.lib.drivers.local import LocalDriver
from sentential.lib.ontology import Ontology

logs = typer.Typer()


@logs.command()
def local(follow: bool = typer.Option(False)):
    """dump running container logs"""
    local = LocalDriver(Ontology())
    local.logs(follow)


@logs.command()
def aws(follow: bool = typer.Option(False)):
    """dump running container logs"""
    aws = AwsDriver(Ontology())
    aws.logs(follow)

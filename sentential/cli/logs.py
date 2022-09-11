import typer
from sentential.lib.aws import Lambda as AwsLambda
from sentential.lib.local import Lambda as LocalLambda

logs = typer.Typer()


@logs.command()
def local(follow: bool = typer.Option(False)):
    """dump running container logs"""
    LocalLambda.deployed().logs(follow)


@logs.command()
def aws(follow: bool = typer.Option(False)):
    """dump running container logs"""
    AwsLambda.deployed().logs(follow)

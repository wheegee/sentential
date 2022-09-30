import typer
from sentential.lib.drivers.local import LocalDriver
from sentential.lib.ontology import Ontology

deploy = typer.Typer()


@deploy.command()
def aws(
    tag: str = typer.Argument(None, envvar="TAG"),
    public_url: bool = typer.Option(False),
):
    """deploy lambda image to aws"""
    local = LocalDriver(Ontology())
    images = local.images()


@deploy.command()
def local(
    tag: str = typer.Argument("latest", envvar="TAG"),
    public_url: bool = typer.Option(default=False),
):
    """build and deploy local lambda container"""
    pass

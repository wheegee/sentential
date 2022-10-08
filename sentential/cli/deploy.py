import typer
from sentential.lib.drivers.aws import AwsDriver
from sentential.lib.drivers.local import LocalDriver
from sentential.lib.ontology import Ontology

deploy = typer.Typer()


@deploy.command()
def local(
    version: str = typer.Argument("latest", envvar="VERSION"),
    public_url: bool = typer.Option(False),
):
    """deploy lambda image to aws"""
    local = LocalDriver(Ontology())
    aws = AwsDriver(Ontology())
    try:
        image = local.image(version)
    except:
        image = aws.image(version)
        local.pull(image)

    print(local.deploy(image, public_url))


@deploy.command()
def aws(
    version: str = typer.Argument(..., envvar="VERSION"),
    public_url: bool = typer.Option(default=False),
):
    """build and deploy local lambda container"""
    aws = AwsDriver(Ontology())
    image = aws.image(version)
    print(aws.deploy(image, public_url))

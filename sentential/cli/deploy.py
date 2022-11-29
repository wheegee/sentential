import typer
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import CURRENT_WORKING_IMAGE_TAG
from sentential.lib.semver import SemVer
from rich import print

deploy = typer.Typer()


@deploy.command()
def local(
    version: str = typer.Argument(CURRENT_WORKING_IMAGE_TAG, envvar="VERSION"),
):
    """build and deploy local lambda container"""
    ontology = Ontology()
    local = LocalLambdaDriver(ontology)
    aws = AwsLambdaDriver(ontology)

    try:
        image = local.image(version)
    except:
        image = aws.image(version)
        local.pull(image)

    function = local.deploy(image)
    print(function)


@deploy.command()
def aws(
    version: str = typer.Argument(None, envvar="VERSION"),
):
    """deploy lambda image to aws"""
    ontology = Ontology()
    aws_lambda = AwsLambdaDriver(ontology)

    if version is None:
        version = SemVer(aws_lambda.images()).latest

    image = aws_lambda.image(version)
    function = aws_lambda.deploy(image)
    print(function)

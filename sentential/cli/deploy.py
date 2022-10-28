import typer
from sentential.lib.drivers.aws_lambda import AwsLambdaDriver
from sentential.lib.drivers.local_lambda import LocalLambdaDriver
from sentential.lib.drivers.aws_api_gateway import AwsApiGatewayDriver
from sentential.lib.ontology import Ontology
from sentential.lib.shapes import CURRENT_WORKING_IMAGE_TAG

deploy = typer.Typer()


@deploy.command()
def local(
    version: str = typer.Argument(CURRENT_WORKING_IMAGE_TAG, envvar="VERSION"),
    public_url: bool = typer.Option(False),
):
    """build and deploy local lambda container"""
    local = LocalLambdaDriver(Ontology())
    aws = AwsLambdaDriver(Ontology())
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
    mount: str = typer.Option(None, autocompletion=AwsApiGatewayDriver.autocomplete),
):
    """deploy lambda image to aws"""
    ontology = Ontology()
    aws_lambda = AwsLambdaDriver(ontology)
    aws_api_gateway = AwsApiGatewayDriver(ontology)
    image = aws_lambda.image(version)
    function = aws_lambda.deploy(image, public_url)
    if mount:
        aws_api_gateway.put_route(mount, function)
    if function.public_url:
        print(function.public_url)


@deploy.command()
def wut():
    print(AwsApiGatewayDriver.sentential_domains())
    print(AwsApiGatewayDriver.autocomplete())

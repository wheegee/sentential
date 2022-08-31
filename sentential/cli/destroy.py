import typer
from sentential.lib.aws import Lambda as AwsLambda
from sentential.lib.aws import Image as AwsImage
from sentential.lib.local import Lambda as LocalLambda
from sentential.lib.local import Image as LocalImage

destroy = typer.Typer()


@destroy.command()
def local(
    tag: str = typer.Argument("latest", envvar="TAG"),
):
    """destroy lambda deployment in aws"""
    lmb = LocalLambda.deployed()
    if lmb:
        lmb.destroy()

@destroy.command()
def aws(
    tag: str = typer.Argument("latest", envvar="TAG"),
):
    """destroy lambda deployment in aws"""
    lmb = AwsLambda.deployed()
    if lmb:
        lmb.destroy()
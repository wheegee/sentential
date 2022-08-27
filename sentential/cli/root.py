import typer
from sentential.lib.shapes.aws import Runtimes
from sentential.lib.template import InitTime
from sentential.lib.local import Image as LocalImage
from sentential.lib.local import Repository as LocalRepository
from sentential.lib.aws import Repository as AwsRepository
import polars as pl
from rich.table import Table
from rich import print

root = typer.Typer()


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """initialize sentential project"""
    InitTime(repository_name).scaffold(f"public.ecr.aws/lambda/{runtime.value}:latest")


@root.command()
def publish(tag: str = typer.Argument("latest", envvar="TAG")):
    """publish lambda image to aws"""
    LocalRepository().publish(LocalImage(tag))

@root.command()
def ls():
    from IPython import embed
    local = LocalRepository().df()
    aws = AwsRepository().df()
    data = local.join(aws, on="Sha", how="outer", suffix="_aws")
    table = Table(*data.columns)
    for row in data.rows():
        
        table.add_row(*[str(value) for value in list(row)])
    print(table)
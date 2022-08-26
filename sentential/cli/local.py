import typer
from sentential.lib.local import Image, Lambda, Repository
import polars as pl

local = typer.Typer()


@local.command()
def deploy(
    tag: str = typer.Argument("latest", envvar="TAG"),
    public_url: bool = typer.Option(default=False),
):
    """build and deploy local lambda container"""
    Lambda(Image(tag)).deploy(public_url)


@local.command()
def destroy(
    tag: str = typer.Argument("latest", envvar="TAG"),
):
    """destroy local lambda container"""
    Lambda(Image(tag)).destroy()


@local.command()
def list():
    """list local lambda images"""
    columns = [
        ("Tag", pl.Utf8),
        ("Arch", pl.Utf8),
        ("Sha", pl.Utf8),
        ("Deployed", pl.Boolean),
    ]
    images = Repository().images()
    deployed = Lambda.deployed()
    table = pl.DataFrame(
        [
            [i.tag for i in images],
            [i.arch for i in images],
            [i.id for i in images],
            [
                "i.id == deployed.image.id" if deployed is not None else False
                for i in images
            ],
        ],
        columns=columns,
    )
    print(table)


@local.command()
def logs(follow: bool = typer.Option(False)):
    """dump running container logs"""
    Lambda.deployed().logs(follow)

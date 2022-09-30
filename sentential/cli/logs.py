import typer

logs = typer.Typer()


@logs.command()
def local(follow: bool = typer.Option(False)):
    """dump running container logs"""
    pass


@logs.command()
def aws(follow: bool = typer.Option(False)):
    """dump running container logs"""
    pass

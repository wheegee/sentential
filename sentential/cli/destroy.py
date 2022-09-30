import typer

destroy = typer.Typer()

@destroy.command()
def local():
    """destroy lambda deployment in aws"""
    pass


@destroy.command()
def aws():
    """destroy lambda deployment in aws"""
    pass

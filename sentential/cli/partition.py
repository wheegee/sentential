import typer

aws = typer.Typer()


@aws.command()
def add(partition: str):
    pass


@aws.command()
def remove(partition: str):
    pass

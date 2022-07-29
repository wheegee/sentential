import typer
from sentential.lib.store import SecretStore

secret = typer.Typer()

@secret.command()
def read():
    """secrets for {repository} lambda"""
    SecretStore().read()


@secret.command()
def write(key: str, value: str):
    """secrets for {repository} lambda"""
    SecretStore.write(key, value)


@secret.command()
def delete(key: str):
    """secrets for {repository} lambda"""
    SecretStore.delete(key)
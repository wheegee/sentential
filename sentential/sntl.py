from enum import Enum
import os
import typer
from sentential.lib.biolerplate import BoilerPlate
from sentential.lib.ops import Ops
from sentential.lib.biolerplate import Runtimes
from IPython import embed

root = typer.Typer()
secrets = typer.Typer()
config = typer.Typer()

try:
    Lambdas = Enum("Lambdas", {name: name for name in os.listdir("lambdas")})
except FileNotFoundError:
    Lambdas = Enum("lambdas", {})

@root.command()
def init(repository: str, runtime: Runtimes):
    """lambdas/{repository}"""
    BoilerPlate(repository).ensure(f"public.ecr.aws/lambda/{runtime.value}:latest")


@root.command()
def build(repository: Lambdas, tag: str = "latest"):
    """lambdas/{repository} with {tag}"""
    Ops(repository.value).build(tag)


@root.command()
def emulate(repository: Lambdas, tag: str = "latest"):
    """lambdas/{repository} locally"""
    Ops(repository.value).emulate(tag)


@root.command()
def publish(repository: Lambdas, tag: str = "latest"):
    """lambdas/{repository} to ecr with {tag}"""
    Ops(repository.value).publish(tag)


@root.command()
def deploy(repository: Lambdas, tag: str = "latest"):
    """{repository}:{tag} from ecr as {repository} to aws"""
    Ops(repository.value).deploy(tag)


@root.command()
def destroy(repository: Lambdas, tag: str = "latest"):
    """{repository} lambda in aws"""
    Ops(repository.value).destroy(tag)


@secrets.command()
def read(repository: Lambdas):
    """secrets for {repository} lambda"""
    Ops(repository.value).secret.read()


@secrets.command()
def write(repository: Lambdas, key: str, value: str):
    """secrets for {repository} lambda"""
    Ops(repository.value).secret.write(key,value)


@secrets.command()
def delete(repository: Lambdas, key: str):
    """secrets for {repository} lambda"""
    Ops(repository.value).secret.delete(key)

@config.command()
def read(repository: Lambdas):
    """config for {repository} lambda"""
    Ops(repository.value).config.read()


@config.command()
def write(repository: Lambdas, key: str, value: str):
    """config for {repository} lambda"""
    Ops(repository.value).config.write(key, value)


@config.command()
def delete(repository: Lambdas, key: str):
    """config for {repository} lambda"""
    Ops(repository.value).config.delete(key)

root.add_typer(secrets, name="secret", help="for {repository}")
root.add_typer(config, name="config", help="for {repository}")

def main():
    root()

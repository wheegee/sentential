import os
import typer
from yaml import safe_load
from sentential.lib.ops import Ops
from sentential.lib.biolerplate import BoilerPlate, Runtimes
from os.path import exists
from IPython import embed

root = typer.Typer()
secrets = typer.Typer()
config = typer.Typer()

repository_name = None
try:
    repository_name = safe_load(open("./sentential.yml"))['repository_name']
except:
    pass


@root.command()
def init(repository_name: str, runtime: Runtimes):
    """lambdas/{repository}"""
    BoilerPlate(repository_name).ensure(runtime)

@root.command()
def build(tag: str = "latest"):
    """lambdas/{repository} with {tag}"""
    Ops(repository_name).build(tag)


@root.command()
def emulate(tag: str = "latest"):
    """lambdas/{repository} locally"""
    Ops(repository_name).emulate(tag)


@root.command()
def publish(tag: str = "latest"):
    """lambdas/{repository} to ecr with {tag}"""
    Ops(repository_name).publish(tag)


@root.command()
def deploy(tag: str = "latest"):
    """{repository}:{tag} from ecr as {repository} to aws"""
    Ops(repository_name).deploy(tag)


@root.command()
def destroy(tag: str = "latest"):
    """{repository} lambda in aws"""
    Ops(repository_name).destroy(tag)


@secrets.command()
def read():
    """secrets for {repository} lambda"""
    Ops(repository_name).secret.read()


@secrets.command()
def write(key: str, value: str):
    """secrets for {repository} lambda"""
    Ops(repository_name).secret.write(key,value)


@secrets.command()
def delete(key: str):
    """secrets for {repository} lambda"""
    Ops(repository_name).secret.delete(key)


@config.command()
def read():
    """config for {repository} lambda"""
    Ops(repository_name).config.read()


@config.command()
def write(key: str, value: str):
    """config for {repository} lambda"""
    Ops(repository_name).config.write(key, value)


@config.command()
def delete(key: str):
    """config for {repository} lambda"""
    Ops(repository_name).config.delete(key)


root.add_typer(secrets, name="secret", help="for {repository}")
root.add_typer(config, name="config", help="for {repository}")


def main():
    root()

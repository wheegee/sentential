from enum import Enum
import os
import typer
from lib.biolerplate import BoilerPlate
from lib.ops import Ops
from lib.biolerplate import Runtimes
from lib.chamber import ChamberWrapper

root = typer.Typer()
secrets = typer.Typer()

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
    ChamberWrapper(repository.value).read()


@secrets.command()
def write(repository: Lambdas, key: str, value: str):
    """secrets for {repository} lambda"""
    ChamberWrapper(repository.value).write(key, value)


@secrets.command()
def delete(repository: Lambdas, key: str):
    """secrets for {repository} lambda"""
    ChamberWrapper(repository.value).delete(key)


root.add_typer(secrets, name="secrets", help="for {repository}")

if __name__ == "__main__":
    root()

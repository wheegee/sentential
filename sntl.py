import typer
from lib.biolerplate import BoilerPlate
from lib.ops import Ops
from lib.biolerplate import Runtimes
from lib.chamber import ChamberWrapper

root = typer.Typer()
secrets = typer.Typer()


@root.command()
def init(repository: str, runtime: Runtimes):
    BoilerPlate(repository).ensure(f"public.ecr.aws/lambda/{runtime.value}:latest")


@root.command()
def build(repository: str, tag: str = "latest"):
    Ops(repository).build(tag)


@root.command()
def emulate(repository: str, tag: str = "latest"):
    Ops(repository).emulate(tag)


@root.command()
def publish(repository: str, tag: str = "latest"):
    Ops(repository).publish(tag)


@root.command()
def deploy(repository: str, tag: str = "latest"):
    Ops(repository).deploy(tag)


@root.command()
def destroy(repository: str, tag: str = "latest"):
    Ops(repository).destroy(tag)


@secrets.command()
def read(repository: str):
    ChamberWrapper(repository).read()


@secrets.command()
def write(repository: str, key: str, value: str):
    ChamberWrapper(repository).write(key, value)


@secrets.command()
def delete(repository: str, key: str):
    ChamberWrapper(repository).delete(key)


root.add_typer(secrets, name="secrets")

if __name__ == "__main__":
    root()

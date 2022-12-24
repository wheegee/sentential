import pytest
from tempfile import TemporaryDirectory
from os import chdir, getcwd
from shutil import copytree
from typer.testing import CliRunner
from sentential.sntl import root as sntl


@pytest.fixture(scope="class")
def invoke():
    runner = CliRunner()

    def invoker(cmd: list):
        return runner.invoke(sntl, cmd)

    return invoker


@pytest.fixture(scope="class")
def init(invoke):
    repo = TemporaryDirectory()
    src = getcwd()
    chdir(repo.name)
    invoke(["init", "test", "python"])
    copytree(f"{src}/tests/fixtures/static", f"{repo.name}/fixtures")
    yield repo.name
    chdir(src)
    repo.cleanup()

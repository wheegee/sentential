import pytest
from tempfile import TemporaryDirectory
from os import chdir, getcwd, remove
from shutil import copyfile
from typer.testing import CliRunner
from sentential.sntl import root as sntl
from sentential.lib.ontology import Ontology


@pytest.fixture(scope="class")
def invoke():
    runner = CliRunner()

    def invoker(cmd: list):
        return runner.invoke(sntl, cmd)

    return invoker


@pytest.fixture(scope="class")
def ontology() -> Ontology:
    return Ontology()


@pytest.fixture(scope="class")
def project() -> str:
    return getcwd()


@pytest.fixture(scope="class")
def repo() -> TemporaryDirectory:
    return TemporaryDirectory()


@pytest.fixture(scope="class")
def init(invoke, project, repo):
    chdir(repo.name)
    invoke(["init", "testing", "python"])
    yield
    chdir(project)
    repo.cleanup()


@pytest.fixture(scope="class")
def shapes(ontology: Ontology, project, repo, invoke):
    copyfile(f"{project}/tests/fixtures/files/shapes.py", f"{repo.name}/shapes.py")
    yield
    remove("shapes.py")
    invoke(["init", "testing", "python"])

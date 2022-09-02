import pytest
from os import getcwd, chdir
from tempfile import TemporaryDirectory
from typer.testing import CliRunner
from sentential.sntl import root as sntl


@pytest.fixture(scope="module")
def project():
    return getcwd()


@pytest.fixture(scope="module")
def repo():
    return TemporaryDirectory()


@pytest.fixture(scope="module")
def invoke():
    runner = CliRunner()

    def invoker(cmd: list):
        return runner.invoke(sntl, cmd)

    return invoker


@pytest.fixture(scope="module", autouse=True)
def run_in_tmp_dir(project, repo):
    chdir(repo.name)
    yield
    chdir(project)
    repo.cleanup()


def pytest_configure():
    pytest.deployment_url = None

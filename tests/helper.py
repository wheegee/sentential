import pytest
from typer.testing import CliRunner
import tempfile
from os import getcwd

runner = CliRunner()
project = getcwd()
repo = tempfile.TemporaryDirectory()


def teardown_module(module):
    repo.cleanup()


@pytest.fixture(autouse=True)
def run_in_tmp_dir(monkeypatch):
    monkeypatch.chdir(repo.name)
    yield
    monkeypatch.chdir(project)
